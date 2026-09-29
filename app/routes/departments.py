"""
Department management (admin only).

Mirrors students.py / teachers.py: every route is protected by
@login_required + @role_required("admin"), enforced on the server - not
just by hiding the sidebar link for other roles.

Deleting a department is deliberately not offered: Course and Teacher both
hard-reference a department through a NOT NULL foreign key, so removing one
would orphan that data.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app import db
from app.models.department import Department
from app.models.course import Course
from app.models.student import Student
from app.utils.decorators import role_required
from app.utils.validators import required

departments_bp = Blueprint("departments", __name__, url_prefix="/admin/departments")


def _student_counts_by_department():
    """{department_id: number of students} computed in one query.

    Students only reference a course, so we go through Course to find
    which department a student belongs to.
    """
    rows = (
        db.session.query(Course.department_id, db.func.count(Student.id))
        .join(Student, Student.course_id == Course.id)
        .group_by(Course.department_id)
        .all()
    )
    return {department_id: count for department_id, count in rows}


@departments_bp.route("/")
@login_required
@role_required("admin")
def list_departments():
    departments = Department.query.order_by(Department.code).all()
    return render_template(
        "departments/list.html",
        departments=departments,
        student_counts=_student_counts_by_department(),
    )


@departments_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_department():
    if request.method == "POST":
        errors = _validate_department_form(request.form, is_new=True)
        if not errors:
            try:
                department = Department(
                    name=request.form["name"].strip(),
                    code=request.form["code"].strip().upper(),
                )
                db.session.add(department)
                db.session.commit()
                flash(f"Department {department.code} added.", "success")
                return redirect(url_for("departments.list_departments"))
            except Exception:
                db.session.rollback()
                errors.append(
                    "Could not save department. Check that the name and code aren't already in use."
                )

        for error in errors:
            flash(error, "danger")
        return render_template("departments/form.html", department=None, form=request.form)

    return render_template("departments/form.html", department=None, form=None)


@departments_bp.route("/<int:department_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)

    if request.method == "POST":
        errors = _validate_department_form(request.form, is_new=False, department=department)
        if not errors:
            try:
                department.name = request.form["name"].strip()
                department.code = request.form["code"].strip().upper()
                db.session.commit()
                flash(f"Department {department.code} updated.", "success")
                return redirect(url_for("departments.list_departments"))
            except Exception:
                db.session.rollback()
                errors.append(
                    "Could not save department. Check that the name and code aren't already in use."
                )

        for error in errors:
            flash(error, "danger")
        return render_template(
            "departments/form.html", department=department, form=request.form
        )

    return render_template("departments/form.html", department=department, form=None)


@departments_bp.route("/<int:department_id>")
@login_required
@role_required("admin")
def view_department(department_id):
    department = Department.query.get_or_404(department_id)
    return render_template("departments/profile.html", department=department)


def _validate_department_form(form, is_new, department=None):
    errors = []

    if not required(form.get("name")):
        errors.append("Department name is required.")
    if not required(form.get("code")):
        errors.append("Department code is required.")

    name = form.get("name", "").strip()
    if name:
        existing = (
            Department.query.filter(db.func.lower(Department.name) == name.lower()).first()
        )
        if existing and (is_new or existing.id != department.id):
            errors.append("That department name is already in use.")

    code = form.get("code", "").strip().upper()
    if code:
        existing = Department.query.filter_by(code=code).first()
        if existing and (is_new or existing.id != department.id):
            errors.append("That department code is already in use.")

    return errors