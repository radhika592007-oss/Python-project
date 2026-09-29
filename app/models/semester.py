from app import db
from app.models.base import TimestampMixin


class Semester(db.Model, TimestampMixin):
    """A single semester (e.g. Semester 3) that belongs to one course."""

    __tablename__ = "semesters"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)  # 1, 2, 3 ...

    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    sections = db.relationship("Section", backref="semester", lazy=True)
    subjects = db.relationship("Subject", backref="semester", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("course_id", "number", name="uq_course_semester"),
    )

    def __repr__(self):
        return f"<Semester {self.number} of course {self.course_id}>"
