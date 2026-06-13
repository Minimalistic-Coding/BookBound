import os
from dotenv import load_dotenv

load_dotenv()

base_dir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(base_dir, "app.db"))
    SECRET_KEY = os.environ.get("SECRET_KEY") or "08d158812e6808a23c0c81d7ccb69dbeb96acb41c8b6fc32c342e9a05e7ad28f"
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['joshuaimran8989@gmail.com', 'joshuaimran6969@gmail.com']

    ITEMS_PER_PAGE = 24

    LANGUAGES = ['en', 'es', 'ru', 'ur', 'ar']