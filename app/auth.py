from flask import Blueprint, request, redirect, url_for
from flask_login import login_user, logout_user, login_required
from .models import User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST", "GET"])
def login():
    # Dummy login for Railway test (no forms/templates)
    email = request.args.get("email", "admin@demo.com")
    password = request.args.get("password", "admin123")

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for("events.home"))

    return "Login failed", 401


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return "Logged out"

