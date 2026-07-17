from flask import render_template, flash, redirect, url_for, request
from flask import g, current_app
from app import db
from app.blueprints.main import bp
from app.blueprints.main.forms import CommentForm, SearchForm
from app.models import User, Book, Comment, Notification
from app.utils.pagination import paginate_elements
from flask_babel import _, get_locale
from flask_login import login_required, current_user
import sqlalchemy as sa
from datetime import datetime, timezone

# ------------------------------------------ GENERAL FUNCTIONS ---------------------------------------------------------

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())

# ------------------------------------------ HOME VIEW FUNCTIONS ---------------------------------------------------------

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    books, next_url, prev_url = paginate_elements(query=Book.query, endpoint='main.index')
    return render_template('index.html', title=_('Home'), books=books.items, next_url=next_url, prev_url=prev_url)

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    search_type = g.search_form.search_type.data

    if search_type == 'books':
        results, total = Book.search(g.search_form.q.data, page, current_app.config['ITEMS_PER_PAGE'])
        template = 'search_book.html'
    else:
        results, total = User.search(g.search_form.q.data, page, current_app.config['ITEMS_PER_PAGE'])
        template = 'search_user.html'

    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1, search_type=search_type) if total > page * current_app.config['ITEMS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1, search_type=search_type) if page > 1 else None

    return render_template(template, title=_('Search'), results=results, total=total, query=g.search_form.q.data, search_type=search_type, next_url=next_url, prev_url=prev_url)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalar(query)
    return [{'name': n.name, 'data': n.get_data(), 'timestamp': n.timestamp} for n in notifications]

# ------------------------------------------ BOOK VIEW FUNCTIONS ---------------------------------------------------------

@bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    form = CommentForm()
    if book is None:
        flash(_("Book Not Available!"))
        return redirect(url_for('main.index'))

    query = book.book_comments.select().order_by(Comment.timestamp.desc())
    comments, next_url, prev_url = paginate_elements(query=query, endpoint='main.book_detail', book_id=book.id)

    return render_template('book.html', title=book.title, book=book, form=form, comments=comments.items, next_url=next_url, prev_url=prev_url)

@bp.route('/book/<int:book_id>/popup')
def book_popup(book_id):
    book = db.session.get(Book, book_id)
    return render_template('book_popup.html', book=book)

# ------------------------------------------ COMMENT VIEW FUNCTIONS ---------------------------------------------------------

@bp.route('/addcomment/<int:book_id>', methods=["POST"])
@login_required
def add_comment(book_id):
    form = CommentForm()
    current_page = url_for('main.book_detail', book_id=book_id)
    if form.validate_on_submit():
        book_obj = db.session.get(Book, book_id)
        if not book_obj:
            return redirect(current_page)

        comment = Comment(body=form.comment.data, author=current_user, book=book_obj)
        db.session.add(comment)
        db.session.commit()

        flash(_('Comment Successfully Uploaded!'))
        return redirect(current_page)
    
    return redirect(current_page)

# ------------------------------------------ COMMENT AJAX FUNCTIONS ---------------------------------------------------------

@bp.route('/delete_comment/<int:comment_id>', methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment and comment.author == current_user:
        db.session.delete(comment)
        db.session.commit()
        return {'success': True}
        
    return {'error': 'Not authorized'}, 403

# ------------------------------------------ FEED VIEW FUNCTIONS ---------------------------------------------------------    

@bp.route('/feed')
@login_required
def feed():
    query = current_user.following_comments()
    comments, next_url, prev_url = paginate_elements(query=query, endpoint='main.feed')
    return render_template("feed.html", title=_("Feed"), comments=comments.items, next_url=next_url, prev_url=prev_url)