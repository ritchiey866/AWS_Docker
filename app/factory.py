import os

from flask import Flask, request, session

from app.blueprints.auth import auth_bp
from app.blueprints.db_admin import db_admin_bp
from app.blueprints.home import home_bp
from app.blueprints.items import items_bp
from app.config import DevelopmentConfig, ProductionConfig
from app.extensions import db, migrate
from app.models.user import User


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    if config_name is None:
        env = os.environ.get("APP_ENV", "development")
        config_name = "production" if env == "production" else "development"

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    app.config.from_object(config_map.get(config_name, DevelopmentConfig))

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(db_admin_bp)

    @app.context_processor
    def inject_current_user():
        user = None
        user_id = session.get("user_id")
        if user_id is not None:
            user = db.session.get(User, user_id)

        endpoint = request.endpoint or ""
        return {
            "current_user": user,
            "current_endpoint": endpoint,
            "show_sidebar": user is not None and endpoint != "auth.login",
            "items_active": endpoint.startswith("items."),
            "db_active": endpoint.startswith("db_admin."),
        }

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
