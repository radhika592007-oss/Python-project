"""
Small reusable pieces shared by every model, so we don't repeat the same
`id` / `created_at` / `updated_at` columns in every single file.
"""

from datetime import datetime
from app import db


class TimestampMixin:
    """Adds created_at / updated_at columns to any model that uses it."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
