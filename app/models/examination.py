from app import db
from app.models.base import TimestampMixin


class Examination(db.Model, TimestampMixin):
    """
    A single exam event for a subject, e.g. "Mid-Term" for "Data
    Structures". Marks are recorded per-student against this exam.
    """

    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # "Internal Assessment", etc.
    exam_type = db.Column(db.String(30), nullable=False)  # internal/mid/final/practical
    max_marks = db.Column(db.Float, nullable=False, default=100)
    exam_date = db.Column(db.Date, nullable=True)

    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)

    marks_records = db.relationship("Marks", backref="examination", lazy=True)

    def __repr__(self):
        return f"<Examination {self.name} ({self.subject_id})>"
