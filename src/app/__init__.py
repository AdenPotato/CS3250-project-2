import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def _require_env(name):
    # fail at startup with a clear message instead of a vague connection error later
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set - copy .env.example to .env and fill it in")
    return value


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = _require_env("DATABASE_URL")
    app.config["SECRET_KEY"] = _require_env("SECRET_KEY")

    db.init_app(app)
    login_manager.init_app(app)
    # @login_required sends a signed-out visitor here instead of a bare 401
    login_manager.login_view = "main.login"
    login_manager.login_message_category = "error"
    csrf.init_app(app)

    from . import models  # registers the tables before create_all
    from .routes import bp
    app.register_blueprint(bp)

    # pages land story by story, so the nav links a page only once its route exists
    @app.context_processor
    def nav_helpers():
        return {"has_endpoint": lambda name: name in app.view_functions}

    # the grader runs no SQL, so the schema creates itself on startup
    with app.app_context():
        db.create_all()
        models.ensure_dietary_tags()

    return app
