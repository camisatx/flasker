import os
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SITE_NAME = 'Flasker'   # Change this to your site's name
    APP_NICKNAME = 'flasker'    # Single word name for app tasks/containers
    ADMINS = ['flasker@joshschertz.com']    # Change this to your email
    REGISTRATION = True     # allow users to register themselves
    IGNORE_EMAIL_CONFIRMATION = False
    TESTING = False

    # Generate: python -c 'import os; print(os.urandom(512))' | xclip -selection c
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chAnGe Me pLeaSE!'

    # API keys
    GOOGLE_API_CLIENT_ID = ''
    GOOGLE_API_CLIENT_SECRET = ''
    MAILGUN_ADDRESS = ''
    MAILGUN_API = ''

    ITEMS_PER_PAGE = 25
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis database
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    OUTBOUND_EMAIL = 'hello@flasker.com'    # Change this to your outbound email
    FEEDBACK_EMAILS = ADMINS    # Email list where contact forms should be sent

    BLOCKED_USERNAMES = [
        'admin', 'python', 'python3', 'postgres', 'sqlite', 'sqlite3', 'root',
        'url', 'ubuntu', 'debian', 'docker', 'flask', 'com', APP_NICKNAME,
    ]


class DevelopmentDockerConfig(BaseConfig):
    # Map this url to 127.0.0.1 within your localhost's DNS
    SERVER_NAME = 'raatum.com:5003'
    # Flask-SQLAlchey extension uses this URI
    # Postgres URI: postgresql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://%s:wrong-horse-battery-staple@postgres:5432/%s' % \
        (BaseConfig.APP_NICKNAME, BaseConfig.APP_NICKNAME)


class DevelopmentConfig(BaseConfig):
    # Map this url to 127.0.0.1 within your localhost's DNS
    SERVER_NAME = 'raatum.com:5003'
    # Flask-SQLAlchey extension uses this URI
    # Postgres URI: postgresql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://%s:wrong-horse-battery-staple@localhost:5433/%s' % \
        (BaseConfig.APP_NICKNAME, BaseConfig.APP_NICKNAME)


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    REDIS_URL = 'redis://'


class ProductionConfig(BaseConfig):
    SERVER_NAME = 'flasker.com'
    # Flask-SQLAlchey extension uses this URI
    # Postgres URI: postgresql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://%s:correct-horse-battery-staple@postgres:5432/%s' % \
        (BaseConfig.APP_NICKNAME, BaseConfig.APP_NICKNAME)

    # Google reCAPTCHA
    RECAPTCHA_SITE_KEY = ''
    RECAPTCHA_SECRET_KEY = ''
