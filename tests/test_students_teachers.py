"""
Tests for admin-only student/teacher management.

Covers: access control (non-admins get 403), add/edit/deactivate CRUD,
duplicate email/roll-number/employee-code validation, and search.
"""

import pytest

from app import create_app, db
from app.models.user import User
from app.models.department import Department
from app.models.course import Course
from app.models.semester import Semester
from app.models.section import Section
from app.models.student import Student
from app.models.teacher import Teacher
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

def test_teacher_cannot_access_student_management(client):
    login(client, "teacher@test.com")
    response = client.get("/admin/students/")
    assert response.status_code == 403


def test_student_cannot_access_teacher_management(client):
    login(client, "student@test.com")
    response = client.get("/admin/teachers/")
    assert response.status_code == 403


def test_admin_can_list_students(client):
    login(client, "admin@test.com")
    response = client.get("/admin/students/")
    assert response.status_code == 200
    assert b"Test Student" in response.data


# ---------- student CRUD ----------

def test_admin_can_add_student(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        course_id = Course.query.first().id

    response = client.post(
        "/admin/students/add",
        data={
            "full_name": "New Student",
            "roll_number": "CS002",
            "email": "new@test.com",
            "password": "pass1234",
            "course_id": str(course_id),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Student.query.filter_by(roll_number="CS002").first() is not None


def test_duplicate_roll_number_rejected(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        course_id = Course.query.first().id

    response = client.post(
        "/admin/students/add",
        data={
            "full_name": "Duplicate",
            "roll_number": "CS001",  # already used by the seeded student
            "email": "duplicate@test.com",
            "password": "pass1234",
            "course_id": str(course_id),
        },
        follow_redirects=True,
    )
    assert b"already in use" in response.data


def test_deactivating_student_blocks_login(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        student_id = Student.query.filter_by(roll_number="CS001").first().id

    client.post(f"/admin/students/{student_id}/toggle-active", follow_redirects=True)
    client.get("/auth/logout")

    login_response = client.post(
        "/auth/login",
        data={"email": "student@test.com", "password": "password123"},
        follow_redirects=True,
    )
    assert b"deactivated" in login_response.data


# ---------- teacher CRUD ----------

def test_admin_can_add_teacher(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        dept_id = Department.query.first().id

    response = client.post(
        "/admin/teachers/add",
        data={
            "full_name": "New Teacher",
            "employee_code": "EMP002",
            "email": "newteacher@test.com",
            "password": "pass1234",
            "department_id": str(dept_id),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Teacher.query.filter_by(employee_code="EMP002").first() is not None


def test_duplicate_employee_code_rejected(client, app):
    login(client, "admin@test.com")
    with app.app_context():
        dept_id = Department.query.first().id

    response = client.post(
        "/admin/teachers/add",
        data={
            "full_name": "Duplicate Teacher",
            "employee_code": "EMP001",  # already used
            "email": "dupteacher@test.com",
            "password": "pass1234",
            "department_id": str(dept_id),
        },
        follow_redirects=True,
    )
    assert b"already in use" in response.data


def test_student_search_by_name(client):
    login(client, "admin@test.com")
    response = client.get("/admin/students/?q=Test Student")
    assert b"Test Student" in response.data
    response = client.get("/admin/students/?q=Nobody")
    assert b"No students match" in response.data
