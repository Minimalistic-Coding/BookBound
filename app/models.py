# dialect://username:password@host:port/database
# For MySQL
# mysql://scott:tiger@localhost/project

from flask import current_app, url_for
from app import db
from app import login
from sqlalchemy import String, SmallInteger, Numeric, Text, ForeignKey
import sqlalchemy as sa
from decimal import Decimal
from sqlalchemy.orm import mapped_column, Mapped, WriteOnlyMapped, relationship 
import sqlalchemy.orm as so
from typing import Optional
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import jwt
from time import time 
import json
import secrets
# import redis
# import rq
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

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = db.paginate(query, page=page, per_page=per_page,
                                error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

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

class User(PaginatedAPIMixin, UserMixin, SearchableMixin, db.Model):

	__searchable__ = ['username']
	__tablename__ = "users"

	# <-------------------- User Attributes ------------------------------>

	id: Mapped[int] = mapped_column(primary_key=True)
	username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
	email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
	password_hash: Mapped[Optional[str]] = mapped_column(String(256)) 

	token: Mapped[Optional[str]] = mapped_column(String(32), index=True, unique=True)
	token_expiration: Mapped[Optional[datetime]]

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def get_token(self, expires_in=3600):
		now = datetime.now(timezone.utc)
		if self.token and self.token_expiration.replace(
				tzinfo=timezone.utc) > now + timedelta(seconds=30):
			return self.token 
		self.token = secrets.token_hex(16)
		self.token_expiration = now + timedelta(seconds=expires_in)
		db.session.add(self)
		return self.token 

	def revoke_token(self):
		self.token_expiration = datetime.now(timezone.utc) - timedelta(seconds=1)

	@staticmethod
	def check_token(token):
		user = db.session.scalar(sa.select(User).where(User.token==token))
		if user is None or user.token_expiration.replace(
				tzinfo=timezone.utc) < datetime.now(timezone.utc):
			return None
		return user

	def to_dict(self, include_email=False):
		data = {
			'id': self.id,
			'username': self.username,
			'last_seen': self.last_seen.replace(
				tzinfo=timezone.utc).isoformat() if self.last_seen else None,
			'about_me': self.about_me,
			'comments_count': self.comments_count(),
			'follower_count': self.followers_count(),
			'following_count': self.following_count(),
			'_links': {
				'self': url_for('api.get_user', id=self.id),
				'followers': url_for('api.get_followers', id=self.id),
				'following': url_for('api.get_following', id=self.id),
				'avatar': url_for('user.static', filename=f'avatars/{self.avatar_id}.svg', _external=True),

			}
		}
		if include_email:
			data['email'] = self.email 
		return data 

	def from_dict(self, data, new_user=False):
		for field in ['username', 'email', 'about_me']:
			if field in data:
				setattr(self, field, data[field])	
		if new_user and 'password' in data:
			self.set_password(data['password'])

	def add_notification(self, name, data):
		db.session.execute(self.notifications.delete().where(
			Notification.name == name))
		n = Notification(name=name, payload_json=json.dumps(data), user=self)
		db.session.add(n)
		return n

	about_me: Mapped[Optional[str]] = mapped_column(String(320))
	last_seen: Mapped[Optional[datetime]] = mapped_column(default= lambda: datetime.now(timezone.utc))
	avatar_id: Mapped[int] = mapped_column(default=1)

	# <-------------------- Messages Support ------------------------------>

	last_message_read_time: Mapped[Optional[datetime]]

	messages_sent: WriteOnlyMapped['Message'] = relationship(foreign_keys='Message.sender_id', back_populates='author')
	messages_received: WriteOnlyMapped['Message'] = relationship(foreign_keys='Message.recipient_id', back_populates='recipient')

	def unread_message_count(self):
		last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
		query = sa.select(Message).where(Message.recipient == self,
										 Message.timestamp > last_read_time)

		return db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))


	# <-------------------- Relationship Attributes ------------------------------>

	user_comments: WriteOnlyMapped['Comment'] = relationship(back_populates="author")
	notifications: WriteOnlyMapped['Notification'] = relationship(back_populates="user")
	tasks: WriteOnlyMapped['Task'] = relationship(back_populates="user")

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

	def comments_count(self):
		query = sa.select(sa.func.count()).select_from(
			self.user_comments.select().subquery())
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

	def get_chat_connection_token(self, expires_in=3600):
		return jwt.encode({'user_id':self.id, 'exp':time() + expires_in},
			current_app.config['SECRET_KEY'],
			algorithm='HS256')

	@staticmethod
	def check_chat_connection_token(token):
		try:
			id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256']).get('user_id')
		except:
			return None
		return db.session.get(User, id)

	def launch_task(self, name, description, *args, **kwargs):
		if not current_app.task_queue:
			return
		rq_job = current_app.task_queue.enqueue(f'app.tasks.{name}', self.id, *args, **kwargs)
		task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
		db.session.add(task)
		return task

	def get_tasks_in_progress(self):
		query = self.tasks.select().where(Task.complete==False)
		return db.session.scalars(query)

	def get_task_in_progress(self, name):
		query = self.tasks.select().where(Task.name == name, Task.complete == False)
		return db.session.scalar(query)

	def __repr__(self):
		return f"User <{self.username}>"

@login.user_loader
def load_user(id):
	return db.session.get(User, int(id))

# ------------------------------------------ BOOK MODEL ---------------------------------------------------------

class Book(PaginatedAPIMixin, SearchableMixin, db.Model):

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

	def to_dict(self):
		data = {
			"id": self.id,
			"title": self.title,
			"price": self.price,
			"rating": self.rating,
			"availability": self.availability,
			"description": self.description, 
			"_links" : {
				"self": url_for("api.get_book", id=self.id), #add route for this
				"cover": self.cover
			}
		}

		return data

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

	def to_dict(self):
		data = {
			"id": self.id,
			"body": self.body,
			"timestamp": self.timestamp.replace(
				tzinfo=timezone.utc).isoformat() if self.timestamp else None,
			"author": self.author.to_dict(),
			"book": self.book.to_dict(),

			"_links" : {
				"author": url_for('api.get_user', id=self.author.id),
				"book": url_for('api.get_book', id=self.book.id) # add route for this
			}
		}

	def __repr__(self):
		return f"Comment <{self.id}, author={self.user_id}>"

# ------------------------------------------ MESSAGING MODEL ---------------------------------------------------------

class Message(db.Model):
	__tablename__ = "messages"

	id: Mapped[int] = mapped_column(primary_key=True)

	sender_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)
	recipient_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)

	body: Mapped[str] = mapped_column(String(2000))
	timestamp: Mapped[datetime] = mapped_column(index=True, default=lambda: datetime.now(timezone.utc))

	author: Mapped[User] = relationship(foreign_keys='Message.sender_id', back_populates='messages_sent')
	recipient: Mapped[User] = relationship(foreign_keys='Message.recipient_id', back_populates='messages_received')

	def __repr__(self):
		return f"<Message {self.id}>"

# ------------------------------------------ MESSAGING MODEL ---------------------------------------------------------

class Notification(db.Model):
	__tablename__ = "notifications"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(128), index=True)
	user_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)
	timestamp: Mapped[float] = mapped_column(index=True, default=time)
	payload_json: Mapped[str] = mapped_column(sa.Text)

	user: Mapped[User] = relationship(back_populates="notifications")

	def get_data(self):
		return json.load(str(self.payload_json))

# ------------------------------------------ BACKGROUND TASKS MODEL ---------------------------------------------------------

class Task(db.Model):
	id: Mapped[str] = mapped_column(String(36), primary_key=True)
	name: Mapped[str] = mapped_column(String(128), index=True)
	description: Mapped[Optional[str]] = mapped_column(String(128))
	user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
	complete: Mapped[bool] = mapped_column(default=False)

	user: Mapped[User] = relationship(back_populates="tasks")

	def get_rq_job(self):
		try:
			rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
		except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError, ImportError):
			return None
		return rq_job

	def get_progress(self):
		job = self.get_rq_job()
		return job.meta.get('progress', 0) if job is not None else 100

# ------------------------------------------ <------> ---------------------------------------------------------