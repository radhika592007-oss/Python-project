from app import db
from app.models.base import TimestampMixin


class Subject(db.Model, TimestampMixin):
    """A subject taught in a specific semester, e.g. 'Data Structures'."""

    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=3)

    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    # The teacher currently assigned to teach this subject. Nullable
    # because a subject can exist before a teacher is assigned to it.
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=True)

    enrollments = db.relationship("Enrollment", backref="subject", lazy=True)
    attendance_records = db.relationship("Attendance", backref="subject", lazy=True)
    examinations = db.relationship("Examination", backref="subject", lazy=True)

    def __repr__(self):
        return f"<Subject {self.code}>"
