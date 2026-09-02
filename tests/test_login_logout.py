import pytest
from database.db import seed_db, get_db
from werkzeug.security import generate_password_hash


def test_login_page_get(client):
    """GET /login should return 200 and show the login form."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome back" in response.data
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data
    # Unauthenticated navbar
    assert b"Sign in" in response.data
    assert b"Get started" in response.data


def test_login_success(client, app):
    """POST /login with valid credentials should authenticate and redirect to profile."""
    with app.app_context():
        seed_db()

    response = client.post(
        "/login",
        data={
            "email": "nitish@example.com",
            "password": "password123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"

    # Verify session
    with client.session_transaction() as session:
        assert session.get("user_id") is not None
        assert session.get("user_name") == "Nitish Kumar"


def test_login_already_authenticated_redirects(client, app):
    """GET /login when already logged in should redirect to profile."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"


def test_login_invalid_password(client, app):
    """POST /login with wrong password should fail with generic error."""
    with app.app_context():
        seed_db()

    response = client.post(
        "/login",
        data={
            "email": "nitish@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data

    with client.session_transaction() as session:
        assert session.get("user_id") is None


def test_login_nonexistent_email(client, app):
    """POST /login with unknown email should fail with generic error."""
    response = client.post(
        "/login",
        data={
            "email": "unknown@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_missing_fields(client):
    """POST /login with missing fields should show error."""
    response = client.post(
        "/login",
        data={
            "email": "",
            "password": "",
        },
    )
    assert response.status_code == 200
    assert b"Email and password are required." in response.data


def test_login_preserves_email_on_error(client):
    """Failed login attempt should retain the entered email in the form."""
    response = client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "wrong",
        },
    )
    assert response.status_code == 200
    assert b'value="test@example.com"' in response.data


def test_logout(client, app):
    """GET /logout should clear the session and redirect to /login."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    with client.session_transaction() as session:
        assert session.get("user_id") is None
        assert session.get("user_name") is None


def test_navbar_auth_state(client):
    """Navbar should show Profile/Sign out when authenticated, Sign in/Get started when logged out."""
    # Logged out
    response = client.get("/")
    assert b"Sign in" in response.data
    assert b"Get started" in response.data
    assert b"Sign out" not in response.data

    # Logged in
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/")
    assert b"Profile" in response.data
    assert b"Sign out" in response.data
    assert b"Get started" not in response.data
