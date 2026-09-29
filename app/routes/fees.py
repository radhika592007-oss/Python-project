"""
Fees & payments management (admin only).

A Fee belongs to one student and records one billing period (e.g.
"Semester 3 Tuition Fee"). Payments against a fee are stored separately
in the Payment table, so a fee can be settled in installments and every
individual payment keeps its own receipt number.

Payment amounts are validated against the fee's pending balance, and the
auto-suggested receipt number makes it easy to keep receipts sequential.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app import db
from app.models.fee import Fee
from app.models.payment import Payment
from app.models.student import Student
from app.utils.decorators import role_required
from app.utils.validators import parse_date, required

fees_bp = Blueprint("fees", __name__, url_prefix="/admin/fees")

PAYMENT_METHODS = ["cash", "card", "upi", "cheque", "bank_transfer"]


def _next_receipt(fee):
    """Suggest the next receipt number for a fee, e.g. RCPT-0003-002."""
    count = Payment.query.filter_by(fee_id=fee.id).count()
    return f"RCPT-{fee.id:04d}-{count + 1:03d}"


def _parse_amount(raw):
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


@fees_bp.route("/")
@login_required
@role_required("admin")
def list_fees():
    query = Fee.query.join(Student, Fee.student_id == Student.id)

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Student.full_name.ilike(like), Student.roll_number.ilike(like))
        )

    fees = query.order_by(Fee.id.desc()).all()

    # status() is a pure-Python helper on the model, so filtering by it
    # happens after the query rather than in SQL.
    status = request.args.get("status", "")
    if status in ("paid", "partial", "pending"):
        fees = [fee for fee in fees if fee.status() == status]

    return render_template(
        "fees/list.html", fees=fees, filters={"q": search, "status": status}
    )


@fees_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_fee():
    students = Student.query.order_by(Student.roll_number).all()

    if request.method == "POST":
        errors = _validate_fee_form(request.form, is_new=True)
        if not errors:
            try:
                fee = Fee(
                    student_id=request.form.get("student_id", type=int),
                    title=request.form["title"].strip(),
                    total_amount=_parse_amount(request.form.get("total_amount")),
                    due_date=parse_date(request.form.get("due_date")),
                )
                db.session.add(fee)
                db.session.commit()
                flash(f"Fee '{fee.title}' added for {fee.student.full_name}.", "success")
                return redirect(url_for("fees.list_fees"))
            except Exception:
                db.session.rollback()
                errors.append("Could not save the fee. Please try again.")

        for error in errors:
            flash(error, "danger")
        return render_template(
            "fees/form.html", fee=None, form=request.form, students=students
        )

    return render_template("fees/form.html", fee=None, form=None, students=students)


@fees_bp.route("/<int:fee_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    students = Student.query.order_by(Student.roll_number).all()

    if request.method == "POST":
        errors = _validate_fee_form(request.form, is_new=False, fee=fee)
        if not errors:
            try:
                fee.student_id = request.form.get("student_id", type=int)
                fee.title = request.form["title"].strip()
                fee.total_amount = _parse_amount(request.form.get("total_amount"))
                fee.due_date = parse_date(request.form.get("due_date"))
                db.session.commit()
                flash(f"Fee '{fee.title}' updated.", "success")
                return redirect(url_for("fees.list_fees"))
            except Exception:
                db.session.rollback()
                errors.append("Could not save the fee. Please try again.")

        for error in errors:
            flash(error, "danger")
        return render_template(
            "fees/form.html", fee=fee, form=request.form, students=students
        )

    return render_template("fees/form.html", fee=fee, form=None, students=students)
@fees_bp.route("/<int:fee_id>")
@login_required
@role_required("admin")
def view_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    return render_template(
        "fees/profile.html",
        fee=fee,
        payment_methods=PAYMENT_METHODS,
        suggested_receipt=_next_receipt(fee),
    )


@fees_bp.route("/<int:fee_id>/payments/add", methods=["POST"])
@login_required
@role_required("admin")
def add_payment(fee_id):
    fee = Fee.query.get_or_404(fee_id)

    errors = []

    amount = _parse_amount(request.form.get("amount"))
    if not amount or amount <= 0:
        errors.append("Payment amount must be greater than zero.")
    elif amount > fee.pending_amount():
        errors.append(f"Amount exceeds the pending balance of {fee.pending_amount():.2f}.")

    method = request.form.get("method", "").strip()
    if method not in PAYMENT_METHODS:
        errors.append("Select a valid payment method.")

    receipt_number = request.form.get("receipt_number", "").strip()
    if not required(receipt_number):
        errors.append("Receipt number is required.")
    elif Payment.query.filter_by(receipt_number=receipt_number).first():
        errors.append("That receipt number is already in use.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("fees.view_fee", fee_id=fee.id))

    try:
        db.session.add(
            Payment(
                fee_id=fee.id,
                amount=amount,
                method=method,
                receipt_number=receipt_number,
            )
        )
        db.session.commit()
        flash(
            f"Payment of {amount:.2f} recorded for '{fee.title}'.",
            "success",
        )
    except Exception:
        db.session.rollback()
        flash("Could not record the payment. Please try again.", "danger")

    return redirect(url_for("fees.view_fee", fee_id=fee.id))


def _validate_fee_form(form, is_new, fee=None):
    errors = []

    if not form.get("student_id", type=int):
        errors.append("Student is required.")

    if not required(form.get("title")):
        errors.append("Fee title is required.")

    total = _parse_amount(form.get("total_amount"))
    if not total or total <= 0:
        errors.append("Total amount must be a number greater than zero.")

    # Never let an edit shrink a fee below what has already been paid.
    if fee is not None and not errors and total < fee.paid_amount():
        errors.append(
            f"Total cannot be less than the {fee.paid_amount():.2f} already paid."
        )

    return errors