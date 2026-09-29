from app import db
from app.models.base import TimestampMixin


class Teacher(db.Model, TimestampMixin):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )

    employee_code = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    designation = db.Column(db.String(50), nullable=True)  # e.g. "Assistant Professor"

    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=False
    )

    is_active_teacher = db.Column(db.Boolean, default=True, nullable=False)

    subjects = db.relationship("Subject", backref="teacher", lazy=True)

    def __repr__(self):
        return f"<Teacher {self.employee_code}>"
