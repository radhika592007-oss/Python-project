from app import db
from app.models.base import TimestampMixin


class Notice(db.Model, TimestampMixin):
    __tablename__ = "notices"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="normal")  # low/normal/high
    expiry_date = db.Column(db.Date, nullable=True)

    # Who is this notice for: "all", "students", "teachers"
    audience = db.Column(db.String(20), nullable=False, default="all")

    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Notice {self.title}>"
