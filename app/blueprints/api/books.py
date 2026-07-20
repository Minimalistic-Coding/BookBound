from flask import url_for, request
import sqlalchemy as sa 
from app.blueprints.api import bp
from app.blueprints.api.errors import bad_request
from app.blueprints.api.auth import token_auth
from app.models import User, Book, Comment
from app import db

@bp.route('/books/<int:id>', methods=["GET"])
def get_book(id):
	return db.get_or_404(Book, id).to_dict()

@bp.route('/books/<int:id>/comments', methods=['GET'])
@token_auth.login_required
def get_book_comments(id):
    book = db.get_or_404(Book, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return Book.to_collection_dict(book.book_comments.select(), page, per_page,
                                   'api.get_book_comments', id=id)