"""
Small, reusable form-validation helpers.

Keeping these separate from the route functions means the routes stay
readable (the "what should happen" logic), while the "is this input
actually valid" logic lives in one place and can be reused by both the
student and teacher forms.
"""

from datetime import datetime


def parse_date(value):
    """Turn an 'YYYY-MM-DD' string from an HTML <input type=date> into
    a Python date, or return None if it's empty/invalid."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def required(value):
    """True if a form field was actually filled in (not blank/whitespace)."""
    return bool(value and value.strip())
