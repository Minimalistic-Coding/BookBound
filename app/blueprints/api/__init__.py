from flask import Blueprint

bp = Blueprint('api', __name__)

from app.blueprints.api import users, books, tokens, errors