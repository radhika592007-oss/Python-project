"""
Main routes.

For Phase 1 this just proves that login + role-based rendering works:
each role sees a different dashboard template. Phases 2 onward will
replace these placeholder pages with real data (student lists,
attendance forms, etc).
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    if current_user.is_admin():
        return render_template("dashboard_admin.html")
    if current_user.is_teacher():
        return render_template("dashboard_teacher.html")
    return render_template("dashboard_student.html")
