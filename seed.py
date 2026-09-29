"""
Seed script for Phase 1.

Creates just enough data to prove that login + role-based routing works
for all three roles: one admin, one teacher, one student.

Later phases will expand this into a much larger, realistic dataset
(section 17 of the spec: departments, subjects, attendance, exams,
fees...). Run it again any time with:

    python seed.py

It is safe to re-run: it clears existing data first so you always start
from a clean, known state.
"""

from datetime import date

from app import create_app, db
from app.models.user import User
from app.models.department import Department
from app.models.course import Course
from app.models.semester import Semester
from app.models.section import Section
from app.models.teacher import Teacher
from app.models.student import Student

app = create_app()

with app.app_context():
    # Start from a clean slate.
    db.drop_all()
    db.create_all()

    # --- departments, courses, semesters, sections ---
    # Two departments/courses so the admin's search and filter dropdowns
    # in Phase 2 have more than one option to actually filter between.
    cse = Department(name="Computer Science & Engineering", code="CSE")
    ece = Department(name="Electronics & Communication", code="ECE")
    db.session.add_all([cse, ece])
    db.session.flush()

    btech_cse = Course(name="B.Tech Computer Science", code="BTCSE", duration_years=4,
                        department_id=cse.id)
    btech_ece = Course(name="B.Tech Electronics", code="BTECE", duration_years=4,
                        department_id=ece.id)
    db.session.add_all([btech_cse, btech_ece])
    db.session.flush()

    sem3_cse = Semester(number=3, course_id=btech_cse.id)
    sem1_ece = Semester(number=1, course_id=btech_ece.id)
    db.session.add_all([sem3_cse, sem1_ece])
    db.session.flush()

    section_a_cse = Section(name="A", semester_id=sem3_cse.id)
    section_b_cse = Section(name="B", semester_id=sem3_cse.id)
    section_a_ece = Section(name="A", semester_id=sem1_ece.id)
    db.session.add_all([section_a_cse, section_b_cse, section_a_ece])
    db.session.flush()

    # --- admin user ---
    admin_user = User(email="admin@college.edu", role="admin")
    admin_user.set_password("admin123")
    db.session.add(admin_user)

    # --- teacher users + profiles ---
    teacher_user = User(email="teacher@college.edu", role="teacher")
    teacher_user.set_password("teacher123")
    db.session.add(teacher_user)
    db.session.flush()

    teacher_profile = Teacher(
        user_id=teacher_user.id,
        employee_code="EMP001",
        full_name="Anita Sharma",
        designation="Assistant Professor",
        department_id=cse.id,
    )
    db.session.add(teacher_profile)

    teacher_user_2 = User(email="teacher2@college.edu", role="teacher")
    teacher_user_2.set_password("teacher123")
    db.session.add(teacher_user_2)
    db.session.flush()

    teacher_profile_2 = Teacher(
        user_id=teacher_user_2.id,
        employee_code="EMP002",
        full_name="Ravi Kumar",
        designation="Associate Professor",
        department_id=ece.id,
    )
    db.session.add(teacher_profile_2)

    # --- student users + profiles ---
    student_user = User(email="student@college.edu", role="student")
    student_user.set_password("student123")
    db.session.add(student_user)
    db.session.flush()

    student_profile = Student(
        user_id=student_user.id,
        roll_number="CSE2024001",
        full_name="Rohan Verma",
        admission_date=date(2024, 8, 1),
        course_id=btech_cse.id,
        current_semester_id=sem3_cse.id,
        section_id=section_a_cse.id,
    )
    db.session.add(student_profile)

    student_user_2 = User(email="student2@college.edu", role="student")
    student_user_2.set_password("student123")
    db.session.add(student_user_2)
    db.session.flush()

    student_profile_2 = Student(
        user_id=student_user_2.id,
        roll_number="ECE2024001",
        full_name="Priya Singh",
        admission_date=date(2024, 8, 1),
        course_id=btech_ece.id,
        current_semester_id=sem1_ece.id,
        section_id=section_a_ece.id,
    )
    db.session.add(student_profile_2)

    db.session.commit()

    print("Seed data created:")
    print("  Admin     -> admin@college.edu    / admin123")
    print("  Teacher 1 -> teacher@college.edu  / teacher123")
    print("  Teacher 2 -> teacher2@college.edu / teacher123")
    print("  Student 1 -> student@college.edu  / student123")
    print("  Student 2 -> student2@college.edu / student123")
