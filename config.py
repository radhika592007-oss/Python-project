"""
Application configuration.

Keeping configuration in one place makes it easy to see every setting
the app depends on, and to override them later (e.g. for tests) without
touching the rest of the code.
"""

import os

# Base directory of the project (folder that contains this file)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Used by Flask to sign session cookies. In a real deployment this
    # should come from an environment variable, never hard-coded.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # SQLite database stored inside the instance/ folder.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "college.db"),
    )

    # We don't need SQLAlchemy's event system; turning it off saves memory
    # and removes a startup warning.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # How long a "remember me" login session lasts.
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours, in seconds
