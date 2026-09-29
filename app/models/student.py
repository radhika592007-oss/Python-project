from app import db
from app.models.base import TimestampMixin


class Student(db.Model, TimestampMixin):
    """
    Personal + academic profile for a student.

    Login info (email/password) lives on the linked User row instead of
    here, so this table only holds student-specific data.
    """

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )

    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    admission_date = db.Column(db.Date, nullable=True)

    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    current_semester_id = db.Column(
        db.Integer, db.ForeignKey("semesters.id"), nullable=True
    )
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=True)

    is_active_student = db.Column(db.Boolean, default=True, nullable=False)

    # course_id and section_id already get a `.course` / `.section` backref
    # from the Course/Section models. current_semester_id needs its own
    # explicit relationship since Semester doesn't declare a matching one.
    current_semester = db.relationship(
        "Semester", foreign_keys=[current_semester_id]
    )

    enrollments = db.relationship("Enrollment", backref="student", lazy=True)
    attendance_records = db.relationship("Attendance", backref="student", lazy=True)
    marks_records = db.relationship("Marks", backref="student", lazy=True)
    fees = db.relationship("Fee", backref="student", lazy=True)

    def __repr__(self):
        return f"<Student {self.roll_number}>"
