from datetime import datetime

from app import db


class Payment(db.Model):
    """A single payment made towards a Fee record."""

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    fee_id = db.Column(db.Integer, db.ForeignKey("fees.id"), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    paid_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    method = db.Column(db.String(30), nullable=True)  # "cash", "card", "upi" ...
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Payment {self.receipt_number} amount={self.amount}>"
