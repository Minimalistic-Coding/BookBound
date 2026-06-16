# dialect://username:password@host:port/database
# For MySQL
# mysql://scott:tiger@localhost/project

from flask import current_app
from app import db
from app import login
from sqlalchemy import String, SmallInteger, Numeric, Text, ForeignKey
import sqlalchemy as sa
from decimal import Decimal
from sqlalchemy.orm import mapped_column, Mapped, WriteOnlyMapped, relationship 
import sqlalchemy.orm as so
from typing import Optional
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import jwt
from time import time 
from app.search import add_to_index, remove_from_index, query_index
"""
{'name': 'Olio', 
'price': 23.88, 
'rating': 1, 
'availabilty': 18, 
'description': "Part fact, part fiction, Tyehimba Jess's much anticipated second book weaves sonnet, song, and narrative to examine the lives of mostly unrecorded African American performers directly before and after the Civil War up to World War I. Olio is an effort to understand how they met, resisted, complicated, co-opted, and sometimes defeated attempts to minstrelize them.So, while Part fact, part fiction, Tyehimba Jess's much anticipated second book weaves sonnet, song, and narrative to examine the lives of mostly unrecorded African American performers directly before and after the Civil War up to World War I. Olio is an effort to understand how they met, resisted, complicated, co-opted, and sometimes defeated attempts to minstrelize them.So, while I lead this choir, I still find thatI'm being led…I'm a missionarymending my faith in the midst of this flock…I toil in their fields of praise. When folks seethese freedmen stand and sing, they hear their Godspeak in tongues. These nine dark mouths sing shelter;they echo a hymn's haven from slavery's weather.Detroit native Tyehimba Jess' first book of poetry, leadbelly, was a winner of the 2004 National Poetry Series. Jess, a Cave Canem and NYU Alumni, has received fellowships from the Whiting Foundation, National Endowment for the Arts, Illinois Arts Council, and the Provincetown Fine Arts Work Center. Jess is also a veteran of the 2000 and 2001 Green Mill Poetry Slam Team. He exhibited his poetry 
at the 2011 TEDxNashville Conference. Jess is an Associate Professor of English at College of Staten Island. ", 
'cover': 'https://books.toscrape.com/media/cache/b1/0e/b10eabab1e1c811a6d47969904fd5755.jpg'}
"""

# ------------------------------------------ Mixin Classes ---------------------------------------------------------

class SearchableMixin:
	@classmethod
	def search(cls, expression, page, per_page):
		ids, total = query_index(cls.__tablename__, expression, page, per_page)
		
		if total == 0 or not ids:
			return [], 0

		when = [(ids[i], i) for i in range(len(ids))]

		query = sa.select(cls).where(cls.id.in_(ids)).order_by(
			db.case(*when, value=cls.id))
		return db.session.scalars(query), total

	@classmethod
	def before_commit(cls, session):
		session._changes = {
			'add': list(session.new),
			'update': list(session.dirty),
			'delete': list(session.deleted)
		}

	@classmethod
	def after_commit(cls, session):
		for obj in session._changes['add']:
			if isinstance(obj, SearchableMixin):
				add_to_index(obj.__tablename__, obj)

		for obj in session._changes['update']:
			if isinstance(obj, SearchableMixin):
				add_to_index(obj.__tablename__, obj)

		for obj in session._changes['delete']:
			if isinstance(obj, SearchableMixin):
				remove_from_index(obj.__tablename__, obj)

		session._changes = None

	@classmethod
	def reindex(cls):
		for obj in db.session.scalars(sa.select(cls)):
			add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

# ------------------------------------------ FOLLOWERS ASSOCIATION TABLE ---------------------------------------------------------

followers = sa.Table(
	"followers",
	db.metadata,
	sa.Column("follower_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
	sa.Column("followed_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True)
)

# ------------------------------------------ USER MODEL ---------------------------------------------------------

class User(UserMixin, SearchableMixin, db.Model):

	__searchable__ = ['username']
	__tablename__ = "users"

	# <-------------------- User Attributes ------------------------------>

	id: Mapped[int] = mapped_column(primary_key=True)
	username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
	email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
	password_hash: Mapped[Optional[str]] = mapped_column(String(256))

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	about_me: Mapped[Optional[str]] = mapped_column(String(320))
	last_seen: Mapped[Optional[datetime]] = mapped_column(default= lambda: datetime.now(timezone.utc))
	avatar_id: Mapped[int] = mapped_column(default=1)

	# <-------------------- Relationship Attributes ------------------------------>

	user_comments: WriteOnlyMapped['Comment'] = relationship(back_populates="author")

	following: WriteOnlyMapped['User'] = relationship(
		secondary=followers,
		primaryjoin=(followers.c.follower_id == id),
		secondaryjoin=(followers.c.followed_id == id),
		back_populates='followers'
	)

	followers: WriteOnlyMapped['User'] = relationship(
		secondary=followers,
		primaryjoin=(followers.c.followed_id == id),
		secondaryjoin=(followers.c.follower_id == id),
		back_populates="following"
	)	

	def follow(self, user):
		if not self.is_following(user):
			self.following.add(user)

	def unfollow(self, user):
		if self.is_following(user):
			self.following.remove(user)

	def is_following(self, user):
		query = self.following.select().where(User.id == user.id)
		return db.session.scalar(query) is not None

	def following_count(self):
		query = sa.select(sa.func.count()).select_from(
			self.following.select().subquery())
		return db.session.scalar(query)

	def followers_count(self):
		query = sa.select(sa.func.count()).select_from(
			self.followers.select().subquery())
		return db.session.scalar(query)

	def following_comments(self):
		Author = so.aliased(User)
		Follower = so.aliased(User)
		return (
			sa.select(Comment)
			.join(Comment.author.of_type(Author))
			.join(Author.followers.of_type(Follower), isouter=True)
			.where(sa.or_(
				Follower.id == self.id,
				Author.id == self.id))
			.group_by(Comment)
			.order_by(Comment.timestamp.desc())
		)

	def get_reset_password_token(self, expires_in=600):
		return jwt.encode({'password_reset':self.id, 'exp':time() + expires_in}, 
			current_app.config['SECRET_KEY'], 
			algorithm='HS256')

	@staticmethod
	def check_reset_password_token(token):
		try:
			id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256']).get('password_reset')
		except:
			return None
		return db.session.get(User, id)

	def __repr__(self):
		return f"User <{self.username}>"

@login.user_loader
def load_user(id):
	return db.session.get(User, int(id))

# ------------------------------------------ BOOK MODEL ---------------------------------------------------------

class Book(SearchableMixin, db.Model):

	__searchable__ = ['title', 'description']
	__tablename__ = "books"

	id: Mapped[int] = mapped_column(primary_key=True)
	title: Mapped[str] = mapped_column(String(450), nullable=False, unique=True)
	price: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
	rating: Mapped[int] = mapped_column(SmallInteger, default=0)
	availability: Mapped[int] = mapped_column(SmallInteger)
	description: Mapped[str] = mapped_column(Text, default="No Description Available for this Book!")
	cover: Mapped[str] = mapped_column(String(500), nullable=False)

	book_comments: WriteOnlyMapped['Comment'] = relationship(back_populates='book')

	def __repr__(self):
		return f"Book <{self.title}>"

# ------------------------------------------ COMMENT MODEL ---------------------------------------------------------

class Comment(db.Model):

	__tablename__ = "comments"

	id: Mapped[int] = mapped_column(primary_key=True)
	body: Mapped[str] = mapped_column(String(1200))
	timestamp: Mapped[datetime] = mapped_column(default= lambda: datetime.now(timezone.utc), index=True)
	user_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)
	book_id: Mapped[int] = mapped_column(ForeignKey(Book.id), index=True)

	book: Mapped['Book'] = relationship(back_populates="book_comments")
	author: Mapped['User'] = relationship(back_populates="user_comments")

	def __repr__(self):
		return f"Comment <{self.id}, author={self.user_id}>"

# ------------------------------------------ <------> ---------------------------------------------------------