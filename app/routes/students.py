"""
Student management (admin only).

Every route here is protected by @login_required + @role_required("admin"),
enforced on the server - not just by hiding the "Students" link in the
sidebar for other roles.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required

from app import db
from app.models.user import User
from app.models.student import Student
from app.models.course import Course
from app.models.semester import Semester
from app.models.section import Section
from app.utils.decorators import role_required
from app.utils.validators import parse_date, required

students_bp = Blueprint("students", __name__, url_prefix="/admin/students")


def _course_choices():
    """Courses with their semesters and sections, nested, for the
    add/edit form's cascading dropdowns."""
    courses = Course.query.order_by(Course.name).all()
    data = []
    for course in courses:
        semesters = []
        for sem in sorted(course.semesters, key=lambda s: s.number):
            sections = [{"id": sec.id, "name": sec.name} for sec in sem.sections]
            semesters.append({"id": sem.id, "number": sem.number, "sections": sections})
        data.append({"id": course.id, "name": course.name, "semesters": semesters})
    return data


@students_bp.route("/")
@login_required
@role_required("admin")
def list_students():
    query = Student.query.join(User)

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Student.full_name.ilike(like), Student.roll_number.ilike(like))
        )

    course_id = request.args.get("course_id", type=int)
    if course_id:
        query = query.filter(Student.course_id == course_id)

    semester_id = request.args.get("semester_id", type=int)
    if semester_id:
        query = query.filter(Student.current_semester_id == semester_id)

    section_id = request.args.get("section_id", type=int)
    if section_id:
        query = query.filter(Student.section_id == section_id)

    status = request.args.get("status", "")
    if status == "active":
        query = query.filter(Student.is_active_student.is_(True))
    elif status == "inactive":
        query = query.filter(Student.is_active_student.is_(False))

    students = query.order_by(Student.roll_number).all()
    courses = Course.query.order_by(Course.name).all()
    semesters = Semester.query.order_by(Semester.number).all()
    sections = Section.query.order_by(Section.name).all()

    return render_template(
        "students/list.html",
        students=students,
        courses=courses,
        semesters=semesters,
        sections=sections,
        filters={
            "q": search,
            "course_id": course_id,
            "semester_id": semester_id,
            "section_id": section_id,
            "status": status,
        },
    )


@students_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_student():
    if request.method == "POST":
        errors = _validate_student_form(request.form, is_new=True)
        if not errors:
            try:
                user = User(email=request.form["email"].strip().lower(), role="student")
                user.set_password(request.form["password"])
                db.session.add(user)
                db.session.flush()  # get user.id before creating the Student

                student = Student(user_id=user.id)
                _apply_student_form(student, request.form)
                db.session.add(student)
                db.session.commit()

                flash(f"Student {student.full_name} added.", "success")
                return redirect(url_for("students.list_students"))
            except Exception:
                db.session.rollback()
                errors.append("Could not save student. Check that the email and roll number aren't already in use.")

        for error in errors:
            flash(error, "danger")
        return render_template(
            "students/form.html", student=None, form=request.form,
            course_data=_course_choices(),
        )

    return render_template(
        "students/form.html", student=None, form={}, course_data=_course_choices()
    )


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == "POST":
        errors = _validate_student_form(request.form, is_new=False, student=student)
        if not errors:
            try:
                student.user.email = request.form["email"].strip().lower()
                new_password = request.form.get("password", "").strip()
                if new_password:
                    student.user.set_password(new_password)

                _apply_student_form(student, request.form)
                db.session.commit()

                flash(f"Student {student.full_name} updated.", "success")
                return redirect(url_for("students.list_students"))
            except Exception:
                db.session.rollback()
                errors.append("Could not save student. Check that the email and roll number aren't already in use.")

        for error in errors:
            flash(error, "danger")
        return render_template(
            "students/form.html", student=student, form=request.form,
            course_data=_course_choices(),
        )

    return render_template(
        "students/form.html", student=student, form=None, course_data=_course_choices()
    )


@students_bp.route("/<int:student_id>/toggle-active", methods=["POST"])
@login_required
@role_required("admin")
def toggle_active(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_active_student = not student.is_active_student
    student.user.is_active_account = student.is_active_student
    db.session.commit()

    state = "activated" if student.is_active_student else "deactivated"
    flash(f"Student {student.full_name} {state}.", "info")
    return redirect(url_for("students.list_students"))


@students_bp.route("/<int:student_id>")
@login_required
@role_required("admin")
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template("students/profile.html", student=student)


def _validate_student_form(form, is_new, student=None):
    errors = []

    if not required(form.get("full_name")):
        errors.append("Full name is required.")
    if not required(form.get("roll_number")):
        errors.append("Roll number is required.")
    if not required(form.get("email")):
        errors.append("Email is required.")
    if is_new and not required(form.get("password")):
        errors.append("Password is required for a new student.")
    if not form.get("course_id", type=int):
        errors.append("Course is required.")

    email = form.get("email", "").strip().lower()
    if email:
        existing = User.query.filter_by(email=email).first()
        if existing and (is_new or existing.id != student.user_id):
            errors.append("That email is already in use by another account.")

    roll_number = form.get("roll_number", "").strip()
    if roll_number:
        existing = Student.query.filter_by(roll_number=roll_number).first()
        if existing and (is_new or existing.id != student.id):
            errors.append("That roll number is already in use.")

    return errors


def _apply_student_form(student, form):
    student.full_name = form["full_name"].strip()
    student.roll_number = form["roll_number"].strip()
    student.date_of_birth = parse_date(form.get("date_of_birth"))
    student.gender = form.get("gender") or None
    student.phone = form.get("phone") or None
    student.address = form.get("address") or None
    student.admission_date = parse_date(form.get("admission_date"))
    student.course_id = form.get("course_id", type=int)
    student.current_semester_id = form.get("semester_id", type=int) or None
    student.section_id = form.get("section_id", type=int) or None
