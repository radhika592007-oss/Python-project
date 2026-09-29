from app import db
from app.models.base import TimestampMixin


class Attendance(db.Model, TimestampMixin):
    """One row = one student's attendance for one subject on one date."""

    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)

    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # "present" or "absent"

    # Which teacher marked it - useful for accountability/audit.
    marked_by_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=True)

    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "subject_id", "date", name="uq_student_subject_date"
        ),
    )

    def __repr__(self):
        return f"<Attendance {self.student_id} {self.subject_id} {self.date} {self.status}>"
