from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth import login_required
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        flash(f"Welcome, {user.username}.", "success")
        return redirect(url_for("home.dashboard"))

    return render_template("login.html")


@auth_bp.route("/account/password", methods=["GET", "POST"])
@login_required
def change_password():
    user = db.session.get(User, session["user_id"])

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not password and not password_confirm:
            return redirect(url_for("home.dashboard"))

        error = User.validate_password(password)
        if error:
            flash(error, "error")
            return render_template("change_password.html")

        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("change_password.html")

        user.set_password(password)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for("home.dashboard"))

    return render_template("change_password.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
