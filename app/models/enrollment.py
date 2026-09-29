from datetime import datetime

from app import db


class Enrollment(db.Model):
    """
    Records that a specific student is taking a specific subject.

    This is a "join table" - it exists purely to connect Student and
    Subject in a many-to-many relationship (one student takes many
    subjects, one subject has many students).
    """

    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)

    enrolled_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("student_id", "subject_id", name="uq_student_subject"),
    )

    def __repr__(self):
        return f"<Enrollment student={self.student_id} subject={self.subject_id}>"
