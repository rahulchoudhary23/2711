from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("You are already signed in.", "info")
        return redirect(url_for("events.home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        elif User.query.filter_by(email=email).first():
            errors.append("An account with that email already exists.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", name=name, email=email)

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already signed in.", "info")
        return redirect(url_for("events.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", email=email)

        login_user(user)
        flash("Welcome back!", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("events.home"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("events.home"))


@auth_bp.route("/account")
@login_required
def account():
    registration_count = len(current_user.registrations)
    return render_template("account.html", registration_count=registration_count)


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not display_name:
            errors.append("Display name is required.")
        if password and len(password) < 8:
            errors.append("New password must be at least 8 characters long.")
        if password and password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("settings.html", display_name=display_name)

        current_user.name = display_name
        if password:
            current_user.set_password(password)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.settings"))

    return render_template("settings.html", display_name=current_user.name)
