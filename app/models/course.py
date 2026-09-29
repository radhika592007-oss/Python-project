from app import db
from app.models.base import TimestampMixin


class Course(db.Model, TimestampMixin):
    """A degree program, e.g. 'B.Tech Computer Science', 4 years long."""

    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    duration_years = db.Column(db.Integer, nullable=False, default=4)

    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=False
    )

    semesters = db.relationship("Semester", backref="course", lazy=True)
    students = db.relationship("Student", backref="course", lazy=True)

    def __repr__(self):
        return f"<Course {self.code}>"
