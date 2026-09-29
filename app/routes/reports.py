"""
Reports (admin only).

A landing page with current headline numbers plus two detailed reports:
students (enrollment + fee totals) and fees (per-fee payment status).
Both detailed reports support CSV export via ?format=csv so the numbers
can be pulled into Excel/Sheets.
"""

import csv
import io

from flask import Blueprint, render_template, request, Response
from flask_login import login_required

from app import db
from app.models.course import Course
from app.models.department import Department
from app.models.fee import Fee
from app.models.payment import Payment
from app.models.student import Student
from app.models.teacher import Teacher
from app.utils.decorators import role_required

reports_bp = Blueprint("reports", __name__, url_prefix="/admin/reports")


def _csv_response(filename, header, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _fee_totals_by_student():
    """{student_id: {billed, paid, pending, status}} across every fee."""
    totals = {}
    for fee in Fee.query.all():
        entry = totals.setdefault(fee.student_id, {"billed": 0.0, "paid": 0.0})
        entry["billed"] += fee.total_amount
        entry["paid"] += fee.paid_amount()

    for entry in totals.values():
        entry["pending"] = round(entry["billed"] - entry["paid"], 2)
        if entry["pending"] <= 0:
            entry["status"] = "paid"
        elif entry["paid"] > 0:
            entry["status"] = "partial"
        else:
            entry["status"] = "pending"
    return totals


@reports_bp.route("/")
@login_required
@role_required("admin")
def index():
    students = Student.query.count()
    teachers = Teacher.query.count()
    departments = Department.query.count()
    courses = Course.query.count()

    billed = float(
        db.session.query(db.func.coalesce(db.func.sum(Fee.total_amount), 0)).scalar()
    )
    collected = float(
        db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).scalar()
    )
    pending = round(billed - collected, 2)

    dept_rows = []
    for department in Department.query.order_by(Department.code).all():
        dept_rows.append(
            {
                "code": department.code,
                "name": department.name,
                "students": sum(len(c.students) for c in department.courses),
                "teachers": len(department.teachers),
                "courses": len(department.courses),
            }
        )

    fee_status_counts = {"paid": 0, "partial": 0, "pending": 0}
    for fee in Fee.query.all():
        fee_status_counts[fee.status()] += 1

    return render_template(
        "reports/index.html",
        counts={
            "students": students,
            "teachers": teachers,
            "departments": departments,
            "courses": courses,
        },
        money={"billed": billed, "collected": collected, "pending": pending},
        dept_rows=dept_rows,
        fee_status_counts=fee_status_counts,
    )
@reports_bp.route("/students")
@login_required
@role_required("admin")
def students_report():
    query = Student.query

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Student.full_name.ilike(like), Student.roll_number.ilike(like))
        )

    department_id = request.args.get("department_id", type=int)
    if department_id:
        query = query.join(Course, Student.course_id == Course.id).filter(
            Course.department_id == department_id
        )

    students = query.order_by(Student.roll_number).all()
    fee_totals = _fee_totals_by_student()
    departments = Department.query.order_by(Department.name).all()

    if request.args.get("format") == "csv":
        header = [
            "Roll Number",
            "Name",
            "Course",
            "Semester",
            "Section",
            "Billed",
            "Paid",
            "Pending",
            "Status",
        ]
        rows = []
        for student in students:
            totals = fee_totals.get(
                student.id,
                {"billed": 0.0, "paid": 0.0, "pending": 0.0, "status": "pending"},
            )
            rows.append(
                [
                    student.roll_number,
                    student.full_name,
                    student.course.name if student.course else "",
                    str(student.current_semester.number) if student.current_semester else "",
                    student.section.name if student.section else "",
                    f"{totals['billed']:.2f}",
                    f"{totals['paid']:.2f}",
                    f"{totals['pending']:.2f}",
                    totals["status"],
                ]
            )
        return _csv_response("students_report.csv", header, rows)

    return render_template(
        "reports/students.html",
        students=students,
        fee_totals=fee_totals,
        departments=departments,
        filters={"q": search, "department_id": department_id},
    )

@reports_bp.route("/fees")
@login_required
@role_required("admin")
def fees_report():
    query = (
        Fee.query.join(Student, Fee.student_id == Student.id).join(
            Course, Student.course_id == Course.id
        )
    )

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Student.full_name.ilike(like), Student.roll_number.ilike(like))
        )

    department_id = request.args.get("department_id", type=int)
    if department_id:
        query = query.filter(Course.department_id == department_id)

    fees = query.order_by(Fee.id.desc()).all()

    status = request.args.get("status", "")
    if status in ("paid", "partial", "pending"):
        fees = [fee for fee in fees if fee.status() == status]

    departments = Department.query.order_by(Department.name).all()

    if request.args.get("format") == "csv":
        header = [
            "Roll Number",
            "Student",
            "Title",
            "Total",
            "Paid",
            "Pending",
            "Status",
            "Due Date",
        ]
        rows = []
        for fee in fees:
            rows.append(
                [
                    fee.student.roll_number,
                    fee.student.full_name,
                    fee.title,
                    f"{fee.total_amount:.2f}",
                    f"{fee.paid_amount():.2f}",
                    f"{fee.pending_amount():.2f}",
                    fee.status(),
                    str(fee.due_date) if fee.due_date else "",
                ]
            )
        return _csv_response("fees_report.csv", header, rows)

    return render_template(
        "reports/fees.html",
        fees=fees,
        departments=departments,
        filters={"q": search, "department_id": department_id, "status": status},
    )