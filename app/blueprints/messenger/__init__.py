from flask import Blueprint

bp = Blueprint('messenger', __name__, template_folder='templates')

from app.blueprints.messenger import routes, events