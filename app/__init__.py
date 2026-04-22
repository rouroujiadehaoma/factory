"""Flask application factory — Chemical Plant Hazardous Waste Management."""
import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_folder = os.path.join(basedir, 'templates')
    static_folder = os.path.join(basedir, 'static')

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import (
        admin,
        alerts,
        api_v1,
        audit_pages,
        auth,
        batches,
        dashboard,
        main,
        reports,
    )

    auth.register_routes(app)
    main.register_routes(app)
    batches.register_routes(app)
    dashboard.register_routes(app)
    alerts.register_routes(app)
    audit_pages.register_routes(app)
    reports.register_routes(app)
    admin.register_routes(app)
    api_v1.register_routes(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return User.query.get(int(user_id))

    return app
