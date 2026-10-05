from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .models import User

bp = Blueprint("auth", __name__)


def _home_for(user):
    if user.role == "employer":
        return url_for("employer.dashboard")
    if user.role == "admin":
        return url_for("admin.dashboard")
    return url_for("candidate.dashboard")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "candidate")
        company = request.form.get("company", "").strip()

        error = None
        if not name or not email or not password:
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif role not in ("candidate", "employer"):
            error = "Invalid role."
        elif role == "employer" and not company:
            error = "Company name is required for employers."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."

        if error:
            flash(error, "danger")
        else:
            user = User(name=name, email=email, role=role, company=company or None)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Welcome, {user.name}!", "success")
            return redirect(_home_for(user))
    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(request.form.get("password", "")):
            flash("Invalid email or password.", "danger")
        elif not user.is_active:
            flash("This account has been deactivated. Contact the administrator.", "danger")
        else:
            login_user(user)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(_home_for(user))
    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
