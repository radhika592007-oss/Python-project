from app import db
from app.models.base import TimestampMixin


class Section(db.Model, TimestampMixin):
    """A class group within a semester, e.g. Section 'A' or 'B'."""

    __tablename__ = "sections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)  # "A", "B", ...

    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    students = db.relationship("Student", backref="section", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("semester_id", "name", name="uq_semester_section"),
    )

    def __repr__(self):
        return f"<Section {self.name}>"
