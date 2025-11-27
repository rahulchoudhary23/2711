import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.Config")

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User, seed_admin, seed_sample_events

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth_bp
    from .events import events_bp
    from .admin import admin_bp

    app.register_blueprint(events_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # 🔥 ADD HOME ROUTE
    @app.route("/")
    def home():
        return "App is live!"

    # Setup database
    with app.app_context():
        db.create_all()
        seed_admin()
        seed_sample_events()

    return app

