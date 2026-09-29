"""
User model.

Every person who can log in (admin, teacher, or student) has exactly one
row here. We keep login-related data (email, password, role) separate
from personal/academic data (which lives in Student / Teacher). This way:
  - a Student row and a Teacher row both "point to" a User row for login
  - changing how login works never touches student/teacher data
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models.base import TimestampMixin


class User(db.Model, UserMixin, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Used to log in. Must be unique across the whole system.
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # Never store the real password - only a salted hash of it.
    password_hash = db.Column(db.String(255), nullable=False)

    # One of: "admin", "teacher", "student"
    role = db.Column(db.String(20), nullable=False)

    # Lets an admin disable an account without deleting it.
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)

    # One-to-one links to the profile tables. `uselist=False` means
    # "this is a single object, not a list" - a normal one-to-one link.
    student_profile = db.relationship(
        "Student", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile = db.relationship(
        "Teacher", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    # Flask-Login checks this before allowing a user to stay logged in.
    @property
    def is_active(self):
        return self.is_active_account

    def is_admin(self):
        return self.role == "admin"

    def is_teacher(self):
        return self.role == "teacher"

    def is_student(self):
        return self.role == "student"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
