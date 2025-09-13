from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from config import Config

# Extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_class: Optional[type] = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class or Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Provide no-op loaders to avoid requiring authentication
    @login_manager.user_loader
    def load_user(user_id):  # type: ignore[unused-argument]
        return None

    @login_manager.request_loader
    def load_user_from_request(req):  # type: ignore[unused-argument]
        return None

    # Register blueprints
    with app.app_context():
        # Import models so migrations can detect them
        from . import models  # noqa: F401

        # Dev convenience: create tables if they don't exist yet
        db.create_all()

        # Load persisted settings
        from .services.settings import load_settings_into_config
        load_settings_into_config()

        # Autodetect models and prefer gemma3:1b if available
        try:
            from .services.ollama import autodetect_and_apply_model_preference
            autodetect_and_apply_model_preference()
        except Exception:
            pass

        from .blueprints.main import main_bp
        from .blueprints.scenarios import scenarios_bp
        from .blueprints.exports import exports_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(scenarios_bp)
        app.register_blueprint(exports_bp)

    return app
