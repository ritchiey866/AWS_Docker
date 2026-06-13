from flask import Blueprint, render_template

from app.auth import login_required

home_bp = Blueprint("home", __name__)


@home_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")
