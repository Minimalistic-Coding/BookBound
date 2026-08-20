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
def get_book_comments(id):
    book = db.get_or_404(Book, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return Book.to_collection_dict(book.book_comments.select(), page, per_page,
                                   'api.get_book_comments', id=id)

@bp.route('/books', methods=["GET"])
def get_books():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return Book.to_collection_dict(sa.select(Book), page, per_page, 'api.get_books')

@bp.route('/books/search', methods=["GET"])
def search_books():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 40)
    query = request.args.get('q', None)
    results = Book.search(query, page, per_page, is_api=True, endpoint='api.get_books')
    return results