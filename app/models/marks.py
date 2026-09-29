from app import db
from app.models.base import TimestampMixin


class Marks(db.Model, TimestampMixin):
    """One student's score in one examination."""

    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    examination_id = db.Column(
        db.Integer, db.ForeignKey("examinations.id"), nullable=False
    )

    marks_obtained = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "examination_id", name="uq_student_examination"
        ),
    )

    def percentage(self):
        max_marks = self.examination.max_marks
        if not max_marks:
            return 0
        return round((self.marks_obtained / max_marks) * 100, 2)

    def grade(self):
        """Simple percentage-to-grade mapping used across the app."""
        pct = self.percentage()
        if pct >= 90:
            return "A+"
        if pct >= 80:
            return "A"
        if pct >= 70:
            return "B"
        if pct >= 60:
            return "C"
        if pct >= 50:
            return "D"
        return "F"

    def is_pass(self):
        return self.percentage() >= 40

    def __repr__(self):
        return f"<Marks student={self.student_id} exam={self.examination_id}>"
