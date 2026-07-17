import os
from dotenv import load_dotenv

load_dotenv()

base_dir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "sqlite:///" + os.path.join(base_dir, "app.db"))
    SECRET_KEY = os.environ.get("SECRET_KEY")
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('ADMINS', '').split(',')

    DOMAINS = os.environ.get('DOMAINS')

    ITEMS_PER_PAGE = 24
    MESSAGES_PER_CHAT = 20

    LANGUAGES = ['en', 'es', 'ru', 'ur', 'ar']
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
    REDIS_URL = os.environ.get('REDIS_URL', None) #or 'redis://'