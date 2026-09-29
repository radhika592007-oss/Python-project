"""
Application factory.

`create_app()` builds and configures the Flask application: it loads the
configuration, binds the database and login manager, makes sure every model
module is imported so SQLAlchemy knows the full schema, registers all
blueprints, and attaches the shared error pages. Both `run.py` and `seed.py`
use it:

    from app import create_app, db

    app = create_app()            # uses config.Config
    app = create_app(TestConfig)  # tests pass their own config

The `db` object exported here is the single SQLAlchemy instance shared by
every model in app/models.
"""

from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import Config

# One SQLAlchemy instance, shared by every model and route.
db = SQLAlchemy()

# One login manager, pointing at the auth blueprint's login page.
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    """Build the Flask app from a config class (defaults to Config)."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Money helper for templates: 50000 -> "50,000.00"
    app.jinja_env.filters["money"] = lambda value: f"{value:,.2f}"

    db.init_app(app)
    login_manager.init_app(app)

    # Import every model module so SQLAlchemy registers the complete
    # metadata (all tables + relationships) before db.create_all() /
    # db.drop_all() are ever called by seed.py or the tests.
    from app.models import (
        attendance,
        course,
        department,
        enrollment,
        examination,
        fee,
        marks,
        notice,
        payment,
        section,
        semester,
        student,
        subject,
        teacher,
        user,
    )

    # Blueprints: auth (login/logout), main (role-based dashboard), and the
    # admin-only management modules (students, teachers, departments, fees,
    # reports).
    from app.routes.auth import auth_bp
    from app.routes.departments import departments_bp
    from app.routes.fees import fees_bp
    from app.routes.main import main_bp
    from app.routes.reports import reports_bp
    from app.routes.students import students_bp
    from app.routes.teachers import teachers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(fees_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(teachers_bp)

    # Friendly error pages (templates in app/templates/errors/).
    app.register_error_handler(403, _forbidden)
    app.register_error_handler(404, _not_found)
    app.register_error_handler(500, _server_error)

    return app


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login hook: turn a session's stored user id back into a User."""
    from app.models.user import User

    return db.session.get(User, int(user_id))


def _forbidden(error):
    return render_template("errors/403.html"), 403


def _not_found(error):
    return render_template("errors/404.html"), 404


def _server_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500