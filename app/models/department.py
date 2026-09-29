from app import db
from app.models.base import TimestampMixin


class Department(db.Model, TimestampMixin):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)  # e.g. "CSE"

    courses = db.relationship("Course", backref="department", lazy=True)
    teachers = db.relationship("Teacher", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.code}>"
