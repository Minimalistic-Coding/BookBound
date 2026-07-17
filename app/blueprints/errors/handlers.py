from app import db
from flask import render_template, request
from app.blueprints.errors import bp
from app.blueprints.api.errors import error_response as api_error_response

# ------------------------------------------ ERROR HANDLING FUNCTIONS ---------------------------------------------------------

def wants_json_response():
    return request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']

@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)

    return render_template("404.html"), 404

@bp.app_errorhandler(500)
def internal_error(error):
    if wants_json_response():
        return api_error_response(404)

    db.session.rollback()
    return render_template("500.html"), 500