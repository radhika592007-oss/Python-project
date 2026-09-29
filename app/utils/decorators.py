"""
Access-control helpers.

Flask-Login's @login_required only checks "is someone logged in?". We
also need "is this THE RIGHT KIND of someone logged in?" (e.g. only
admins can add a teacher). role_required() adds that second check.

This is enforced on the server for every route that uses it - hiding a
button in the template is never enough on its own, because a user could
still type the URL directly into the browser.
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*allowed_roles):
    """
    Usage:
        @role_required("admin")
        def add_student(): ...

        @role_required("admin", "teacher")
        def view_attendance(): ...
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in allowed_roles:
                abort(403)
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator
