import pytest
from werkzeug.security import check_password_hash
from database.db import get_db


def test_register_page_get(client):
    """GET /register should return 200 and render the registration form."""
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b'name="name"' in response.data
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data


def test_register_success(client, app):
    """POST /register with valid details should create user and redirect to login."""
    response = client.post(
        "/register",
        data={
            "name": "Aarav Sharma",
            "email": "aarav@example.com",
            "password": "securepassword123",
        },
        follow_redirects=False,
    )

    # Should redirect to /login
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    # Verify user in database
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", ("aarav@example.com",)).fetchone()
        assert user is not None
        assert user["name"] == "Aarav Sharma"
        assert user["email"] == "aarav@example.com"
        assert user["password_hash"] != "securepassword123"
        assert check_password_hash(user["password_hash"], "securepassword123")


def test_register_missing_name(client):
    """POST /register without name should return validation error."""
    response = client.post(
        "/register",
        data={
            "name": "   ",
            "email": "aarav@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    assert b"Full name is required." in response.data


def test_register_invalid_email(client):
    """POST /register with invalid or empty email should return validation error."""
    response = client.post(
        "/register",
        data={
            "name": "Aarav Sharma",
            "email": "invalidemail",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    assert b"A valid email address is required." in response.data


def test_register_short_password(client):
    """POST /register with password shorter than 8 characters should return validation error."""
    response = client.post(
        "/register",
        data={
            "name": "Aarav Sharma",
            "email": "aarav@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data


def test_register_duplicate_email(client):
    """POST /register with already registered email should return user-friendly error."""
    # Register first user
    client.post(
        "/register",
        data={
            "name": "User One",
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    # Attempt to register second user with same email (case-insensitive)
    response = client.post(
        "/register",
        data={
            "name": "User Two",
            "email": "DUPLICATE@EXAMPLE.COM",
            "password": "password456",
        },
    )
    assert response.status_code == 200
    assert b"An account with this email already exists." in response.data


def test_register_preserves_form_values_on_error(client):
    """On validation failure, entered name and email should be retained in the form."""
    response = client.post(
        "/register",
        data={
            "name": "Aarav Sharma",
            "email": "aarav@example.com",
            "password": "123",  # triggers length error
        },
    )
    assert response.status_code == 200
    assert b'value="Aarav Sharma"' in response.data
    assert b'value="aarav@example.com"' in response.data
