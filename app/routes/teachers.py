"""
Teacher management (admin only). Mirrors students.py - see that file for
more detailed comments on the pattern being followed.

Subject assignment ("Assign subjects" from the spec) is deferred to
Phase 3, once Subject management exists - a teacher's profile page
already shows an "Assigned subjects" section that will populate once
subjects can be created.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_required

from app import db
from app.models.user import User
from app.models.teacher import Teacher
from app.models.department import Department
from app.utils.decorators import role_required
from app.utils.validators import required

teachers_bp = Blueprint("teachers", __name__, url_prefix="/admin/teachers")


@teachers_bp.route("/")
@login_required
@role_required("admin")
def list_teachers():
    query = Teacher.query.join(User)

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Teacher.full_name.ilike(like), Teacher.employee_code.ilike(like))
        )

    department_id = request.args.get("department_id", type=int)
    if department_id:
        query = query.filter(Teacher.department_id == department_id)

    status = request.args.get("status", "")
    if status == "active":
        query = query.filter(Teacher.is_active_teacher.is_(True))
    elif status == "inactive":
        query = query.filter(Teacher.is_active_teacher.is_(False))

    teachers = query.order_by(Teacher.full_name).all()
    departments = Department.query.order_by(Department.name).all()

    return render_template(
        "teachers/list.html",
        teachers=teachers,
        departments=departments,
        filters={"q": search, "department_id": department_id, "status": status},
    )


@teachers_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_teacher():
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        errors = _validate_teacher_form(request.form, is_new=True)
        if not errors:
            try:
                user = User(email=request.form["email"].strip().lower(), role="teacher")
                user.set_password(request.form["password"])
                db.session.add(user)
                db.session.flush()

                teacher = Teacher(user_id=user.id)
                _apply_teacher_form(teacher, request.form)
                db.session.add(teacher)
                db.session.commit()

                flash(f"Teacher {teacher.full_name} added.", "success")
                return redirect(url_for("teachers.list_teachers"))
            except Exception:
                db.session.rollback()
                errors.append("Could not save teacher. Check that the email and employee code aren't already in use.")

        for error in errors:
            flash(error, "danger")
        return render_template(
            "teachers/form.html", teacher=None, form=request.form, departments=departments
        )

    return render_template(
        "teachers/form.html", teacher=None, form={}, departments=departments
    )


@teachers_bp.route("/<int:teacher_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        errors = _validate_teacher_form(request.form, is_new=False, teacher=teacher)
        if not errors:
            try:
                teacher.user.email = request.form["email"].strip().lower()
                new_password = request.form.get("password", "").strip()
                if new_password:
                    teacher.user.set_password(new_password)

                _apply_teacher_form(teacher, request.form)
                db.session.commit()

                flash(f"Teacher {teacher.full_name} updated.", "success")
                return redirect(url_for("teachers.list_teachers"))
            except Exception:
                db.session.rollback()
                errors.append("Could not save teacher. Check that the email and employee code aren't already in use.")

        for error in errors:
            flash(error, "danger")
        return render_template(
            "teachers/form.html", teacher=teacher, form=request.form, departments=departments
        )

    return render_template(
        "teachers/form.html", teacher=teacher, form=None, departments=departments
    )


@teachers_bp.route("/<int:teacher_id>/toggle-active", methods=["POST"])
@login_required
@role_required("admin")
def toggle_active(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.is_active_teacher = not teacher.is_active_teacher
    teacher.user.is_active_account = teacher.is_active_teacher
    db.session.commit()

    state = "activated" if teacher.is_active_teacher else "deactivated"
    flash(f"Teacher {teacher.full_name} {state}.", "info")
    return redirect(url_for("teachers.list_teachers"))


@teachers_bp.route("/<int:teacher_id>")
@login_required
@role_required("admin")
def view_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    return render_template("teachers/profile.html", teacher=teacher)


def _validate_teacher_form(form, is_new, teacher=None):
    errors = []

    if not required(form.get("full_name")):
        errors.append("Full name is required.")
    if not required(form.get("employee_code")):
        errors.append("Employee code is required.")
    if not required(form.get("email")):
        errors.append("Email is required.")
    if is_new and not required(form.get("password")):
        errors.append("Password is required for a new teacher.")
    if not form.get("department_id", type=int):
        errors.append("Department is required.")

    email = form.get("email", "").strip().lower()
    if email:
        existing = User.query.filter_by(email=email).first()
        if existing and (is_new or existing.id != teacher.user_id):
            errors.append("That email is already in use by another account.")

    employee_code = form.get("employee_code", "").strip()
    if employee_code:
        existing = Teacher.query.filter_by(employee_code=employee_code).first()
        if existing and (is_new or existing.id != teacher.id):
            errors.append("That employee code is already in use.")

    return errors


def _apply_teacher_form(teacher, form):
    teacher.full_name = form["full_name"].strip()
    teacher.employee_code = form["employee_code"].strip()
    teacher.phone = form.get("phone") or None
    teacher.designation = form.get("designation") or None
    teacher.department_id = form.get("department_id", type=int)
