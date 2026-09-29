"""
Tests for the departments, fees, and reports modules.

Run with:  pytest

Covers: admin-only access control, department CRUD + duplicate checks,
fee creation, payment recording (with overpayment + duplicate-receipt
rejection), and report rendering / CSV export.
"""

from datetime import date

import pytest

from app import create_app, db
from app.models.user import User
from app.models.department import Department
from app.models.course import Course
from app.models.semester import Semester
from app.models.section import Section
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.fee import Fee
from app.models.payment import Payment
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

        admin = User(email="admin@test.com", role="admin")
        admin.set_password("password123")
        db.session.add(admin)

        teacher_user = User(email="teacher@test.com", role="teacher")
        teacher_user.set_password("password123")
        db.session.add(teacher_user)
        db.session.flush()

        dept = Department(name="Computer Science", code="CS")
        db.session.add(dept)
        db.session.flush()

        teacher = Teacher(
            user_id=teacher_user.id, employee_code="EMP001",
            full_name="Test Teacher", department_id=dept.id,
        )
        db.session.add(teacher)

        course = Course(name="B.Tech CS", code="BTCS", department_id=dept.id)
        db.session.add(course)
        db.session.flush()

        semester = Semester(number=1, course_id=course.id)
        db.session.add(semester)
        db.session.flush()

        section = Section(name="A", semester_id=semester.id)
        db.session.add(section)
        db.session.flush()

        student_user = User(email="student@test.com", role="student")
        student_user.set_password("password123")
        db.session.add(student_user)
        db.session.flush()

        student = Student(
            user_id=student_user.id, roll_number="CS001",
            full_name="Test Student", course_id=course.id,
            current_semester_id=semester.id, section_id=section.id,
        )
        db.session.add(student)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password="password123"):
    return client.post("/auth/login", data={"email": email, "password": password})


# ---------- access control ----------

def test_teacher_cannot_access_departments(client):
    login(client, "teacher@test.com")
    assert client.get("/admin/departments/").status_code == 403


def test_teacher_cannot_access_fees(client):
    login(client, "teacher@test.com")
    assert client.get("/admin/fees/").status_code == 403


def test_teacher_cannot_access_reports(client):
    login(client, "teacher@test.com")
    assert client.get("/admin/reports/").status_code == 403


# ---------- departments ----------

def test_admin_can_list_departments(client):
    login(client, "admin@test.com")
    response = client.get("/admin/departments/")
    assert response.status_code == 200
    assert b"Computer Science" in response.data


def test_admin_can_add_department(client, app):
    login(client, "admin@test.com")
    response = client.post(
        "/admin/departments/add",
        data={"name": "Mechanical Engineering", "code": "ME"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Department.query.filter_by(code="ME").first() is not None


def test_duplicate_department_code_rejected(client):
    login(client, "admin@test.com")
    response = client.post(
        "/admin/departments/add",
        data={"name": "Another CS", "code": "CS"},  # CS already used
        follow_redirects=True,
    )
    assert b"already in use" in response.data


def test_admin_can_edit_department(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        dept_id = Department.query.first().id

    response = client.post(
        f"/admin/departments/{dept_id}/edit",
        data={"name": "Computer Engineering", "code": "CE"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        dept = db.session.get(Department, dept_id)
        assert dept.name == "Computer Engineering"
        assert dept.code == "CE"


# ---------- fees ----------

def test_admin_can_add_fee(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        student_id = Student.query.first().id

    response = client.post(
        "/admin/fees/add",
        data={
            "student_id": str(student_id),
            "title": "Semester 1 Fees",
            "total_amount": "1000",
            "due_date": "2025-12-01",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        fee = Fee.query.filter_by(title="Semester 1 Fees").first()
        assert fee is not None
        assert fee.total_amount == 1000.0
        assert fee.due_date == date(2025, 12, 1)


def test_record_payment_updates_balance(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        student = Student.query.first()
        fee = Fee(student_id=student.id, title="Sem 4 Fees", total_amount=500)
        db.session.add(fee)
        db.session.commit()
        fee_id = fee.id

    response = client.post(
        f"/admin/fees/{fee_id}/payments/add",
        data={"amount": "200", "method": "upi", "receipt_number": "RCPT-TEST-001"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        fee = db.session.get(Fee, fee_id)
        assert fee.paid_amount() == 200.0
        assert fee.pending_amount() == 300.0
        assert fee.status() == "partial"


def test_payment_cannot_exceed_pending(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        student = Student.query.first()
        fee = Fee(student_id=student.id, title="Small Fee", total_amount=100)
        db.session.add(fee)
        db.session.commit()
        fee_id = fee.id

    response = client.post(
        f"/admin/fees/{fee_id}/payments/add",
        data={"amount": "99999", "method": "cash", "receipt_number": "RCPT-BIG-001"},
        follow_redirects=True,
    )
    assert b"exceeds the pending balance" in response.data
    with app.app_context():
        assert Payment.query.count() == 0


def test_duplicate_receipt_rejected(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        student = Student.query.first()
        fee = Fee(student_id=student.id, title="Dupe Receipt Fee", total_amount=500)
        db.session.add(fee)
        db.session.flush()
        db.session.add(
            Payment(fee_id=fee.id, amount=100, method="cash",
                    receipt_number="RCPT-DUP-001")
        )
        db.session.commit()
        fee_id = fee.id

    response = client.post(
        f"/admin/fees/{fee_id}/payments/add",
        data={"amount": "50", "method": "cash", "receipt_number": "RCPT-DUP-001"},
        follow_redirects=True,
    )
    assert b"already in use" in response.data


# ---------- reports ----------

def test_reports_index_shows_totals(client):
    login(client, "admin@test.com")
    response = client.get("/admin/reports/")
    assert response.status_code == 200
    assert b"Students" in response.data
    assert b"Departments" in response.data


def test_students_report_lists_students(client):
    login(client, "admin@test.com")
    response = client.get("/admin/reports/students")
    assert response.status_code == 200
    assert b"Test Student" in response.data


def test_students_report_csv_export(client):
    login(client, "admin@test.com")
    response = client.get("/admin/reports/students?format=csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"Roll Number" in response.data      # header
    assert b"CS001" in response.data


def test_fees_report_csv_export(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        student = Student.query.first()
        fee = Fee(student_id=student.id, title="CSV Fee", total_amount=250)
        db.session.add(fee)
        db.session.commit()

    response = client.get("/admin/reports/fees?format=csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"CSV Fee" in response.data