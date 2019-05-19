import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
#from flask_wtf.csrf import CSRFProtect
from redis import Redis
import rq


db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
#csrf = CSRFProtect()
login = LoginManager()
login.login_view = 'auth.login'  # Redirect to the login view
login.login_message = 'Please log in to access this page.'
login.session_protection = 'strong'
mail = Mail()
moment = Moment()

app_settings = os.getenv('APP_SETTINGS') or 'config.DevelopmentConfig'


def create_app(config_class=app_settings):
    app = Flask(__name__, subdomain_matching=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    #cors = CORS(app)
    #csrf.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('%s-tasks' % app.config['APP_NICKNAME'], connection=app.redis)

    from app.api.v1 import bp as api_v1_bp    # NOQA
    app.register_blueprint(api_v1_bp, subdomain='api', url_prefix='/v1')

    if not app.debug and not app.testing:
        # Logging code
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/contacts.log', maxBytes=10240,
                backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('%s is starting up' % app.config['SITE_NAME'])

        # Mailing code
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'],
                subject='%s Failure' % app.config['SITE_NAME'],
                credentials=auth, secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

    return app


def create_test_app(config_class=app_settings):
    """Use only for unittests"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    moment.init_app(app)

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('%s-tasks' % app.config['APP_NICKNAME'], connection=app.redis)

    from app.api.v1 import bp as api_v1_bp    # NOQA
    app.register_blueprint(api_v1_bp, url_prefix='/v1')

    return app

# At the bottom to prevent circular imports
from app import models  # NOQA
