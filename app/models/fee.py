from app import db
from app.models.base import TimestampMixin


class Fee(db.Model, TimestampMixin):
    """
    A fee record for one student, for one billing period (e.g. one
    semester). Payments made against this fee are tracked separately in
    the Payment table so we keep a full payment history.
    """

    __tablename__ = "fees"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    title = db.Column(db.String(100), nullable=False)  # "Semester 3 Fees"
    total_amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=True)

    payments = db.relationship("Payment", backref="fee", lazy=True)

    def paid_amount(self):
        return sum(p.amount for p in self.payments)

    def pending_amount(self):
        return round(self.total_amount - self.paid_amount(), 2)

    def status(self):
        if self.pending_amount() <= 0:
            return "paid"
        if self.paid_amount() > 0:
            return "partial"
        return "pending"

    def __repr__(self):
        return f"<Fee {self.title} student={self.student_id}>"
