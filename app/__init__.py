from flask import Flask, request, session, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from elasticsearch import Elasticsearch

# ------------------------------------------ General Shared Functions ---------------------------------------------------------

def get_locale():
	lang = session.get('language')
	if lang in current_app.config['LANGUAGES']:
		return lang
	
	return request.accept_languages.best_match(current_app.config['LANGUAGES'])

# ------------------------------------------ Initializing FLASK-EXTENSIONS ---------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.') 
mail = Mail()
moment = Moment()
babel = Babel()

# ------------------------------------------ Initializing Flask App Function ---------------------------------------------------------

def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(config_class)

	db.init_app(app)
	migrate.init_app(app, db)
	login.init_app(app)
	mail.init_app(app)
	moment.init_app(app)
	babel.init_app(app, locale_selector=get_locale)

	app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']], request_timeout=30) if app.config['ELASTICSEARCH_URL'] else None

	# ------------------------------------------ Initializing FLASK-BLUEPRINTS ---------------------------------------------------------

	# Initializing Errors Blueprint
	from app.blueprints.errors import bp as errors_bp
	app.register_blueprint(errors_bp, url_prefix='/error')

	# Initializing Authentication+Authorization Blueprint
	from app.blueprints.auth import bp as auth_bp
	app.register_blueprint(auth_bp, url_prefix='/auth')

	# Initializing Main Functionality Blueprint
	from app.blueprints.main import bp as main_bp
	app.register_blueprint(main_bp, url_prefix='/main')

	# Initializing User Functionality + Interaction Blueprint
	from app.blueprints.user import bp as user_bp
	app.register_blueprint(user_bp, url_prefix='/user')

	# Initializing CLI Functions Blueprint
	from app.cli import bp as cli_bp
	app.register_blueprint(cli_bp)

	# ------------------------------------------ EMAIL ERROR MONITORING ---------------------------------------------------------

	if not app.debug and not app.testing:

		if app.config["MAIL_SERVER"]:
			auth = None
			if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
				auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])

			secure = None
			if app.config["MAIL_USE_TLS"]:
				secure = ()

			mail_handler = SMTPHandler(
				mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
				fromaddr='no-reply@' + app.config["MAIL_SERVER"],
				toaddrs=app.config["ADMINS"],
				subject="BookBound Failure!",
				credentials=auth,
				secure=secure
			)

			mail_handler.setLevel(logging.ERROR)
			app.logger.addHandler(mail_handler)

	# ------------------------------------------ LOGGING FILE ERROR MONITORING ---------------------------------------------------------

			if not os.path.exists("logs"):
				os.mkdir("logs")

			file_handler = RotatingFileHandler('logs/bookbound.log', maxBytes=10240, backupCount=10)
			file_handler.setFormatter(logging.Formatter(
				'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
			file_handler.setLevel(logging.INFO)
			app.logger.addHandler(file_handler)

			app.logger.setLevel(logging.INFO)
			app.logger.info('BookBound startup')

	return app


from app import models