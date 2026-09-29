"""
Basic authentication tests.

Run with:  pytest

These use an in-memory SQLite database (see the `app` fixture) so they
never touch your real instance/college.db file.
"""

import pytest

from app import create_app, db
from app.models.user import User
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

        user = User(email="admin@test.com", role="admin")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_dashboard_requires_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_with_correct_credentials(client):
    response = client.post(
        "/auth/login",
        data={"email": "admin@test.com", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data


def test_login_with_wrong_password(client):
    response = client.post(
        "/auth/login",
        data={"email": "admin@test.com", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_login_with_unknown_email(client):
    response = client.post(
        "/auth/login",
        data={"email": "nobody@test.com", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_logout_then_dashboard_redirects_to_login(client):
    client.post(
        "/auth/login",
        data={"email": "admin@test.com", "password": "password123"},
    )
    client.get("/auth/logout")
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_password_is_never_stored_in_plain_text(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@test.com").first()
        assert user.password_hash != "password123"
        assert user.check_password("password123") is True
        assert user.check_password("wrong") is False
