"""
Login / logout routes.

We deliberately do NOT provide a public "register" page. In a real
college, accounts are created by the admin (or by the seed script for
this demo) - students and teachers don't sign themselves up.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If someone is already logged in, send them straight to their
    # dashboard instead of showing the login form again.
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None
        if not email or not password:
            error = "Please enter both email and password."
        else:
            user = User.query.filter_by(email=email).first()
            if user is None or not user.check_password(password):
                error = "Invalid email or password."
            elif not user.is_active_account:
                error = "This account has been deactivated. Contact the admin."

        if error:
            flash(error, "danger")
            return render_template("auth/login.html", email=email)

        login_user(user)
        flash(f"Welcome back, {user.email}!", "success")

        # If the user tried to visit a protected page before logging in,
        # Flask-Login stashes that URL in ?next= - send them back there.
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
