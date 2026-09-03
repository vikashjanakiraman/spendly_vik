import pytest
from database.db import seed_db, get_db
from werkzeug.security import check_password_hash, generate_password_hash


def test_profile_unauthenticated_redirect(client):
    """GET /profile, POST /profile, and POST /profile/password without session should redirect to /login."""
    response_get = client.get("/profile", follow_redirects=False)
    assert response_get.status_code == 302
    assert response_headers_contain_login(response_get)

    response_post = client.post("/profile", data={"name": "Test", "email": "test@test.com"}, follow_redirects=False)
    assert response_post.status_code == 302
    assert response_headers_contain_login(response_post)

    response_pwd = client.post("/profile/password", data={"current_password": "a", "new_password": "b", "confirm_password": "b"}, follow_redirects=False)
    assert response_pwd.status_code == 302
    assert response_headers_contain_login(response_pwd)


def response_headers_contain_login(response):
    return "/login" in response.headers.get("Location", "")


def test_profile_authenticated_get(client, app):
    """GET /profile with active session should render user details and stats."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Nitish Kumar" in response.data
    assert b"nitish@example.com" in response.data
    assert b"Total Expenses" in response.data
    assert b"Total Spent" in response.data
    assert b"Spending by Category" in response.data
    assert b"Recent Transactions" in response.data
    # Nitish has 5 sample expenses in seed_db summing to 6400.50
    assert b"5" in response.data
    assert b"6,400.50" in response.data
    assert b"Groceries" in response.data
    assert b"Dinner with friends" in response.data


def test_profile_update_success(client, app):
    """POST /profile with valid data should update DB, update session, and redirect."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile",
        data={
            "name": "Nitish K. Verma",
            "email": "nitish.verma@example.com",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    # Verify session updated
    with client.session_transaction() as session:
        assert session["user_name"] == "Nitish K. Verma"

    # Verify database updated
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert user["name"] == "Nitish K. Verma"
        assert user["email"] == "nitish.verma@example.com"

    # Verify flash message on redirect
    follow_resp = client.get("/profile")
    assert b"Profile updated successfully." in follow_resp.data


def test_profile_update_keep_same_email(client, app):
    """Updating name while keeping the same email should succeed."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile",
        data={
            "name": "Nitish Updated",
            "email": "nitish@example.com",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert user["name"] == "Nitish Updated"
        assert user["email"] == "nitish@example.com"


def test_profile_update_duplicate_email(client, app):
    """POST /profile with another user's email should fail with an error."""
    with app.app_context():
        seed_db()
        db = get_db()
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Second User", "second@example.com", generate_password_hash("pass12345")),
        )
        db.commit()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile",
        data={
            "name": "Nitish Kumar",
            "email": "second@example.com",
        },
    )

    assert response.status_code == 200
    assert b"An account with this email already exists." in response.data

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert user["email"] == "nitish@example.com"


def test_profile_update_validation_errors(client, app):
    """POST /profile with empty name or invalid email should return validation errors."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # Empty name
    resp1 = client.post("/profile", data={"name": "", "email": "nitish@example.com"})
    assert resp1.status_code == 200
    assert b"Full name is required." in resp1.data

    # Invalid email
    resp2 = client.post("/profile", data={"name": "Nitish", "email": "invalidemail"})
    assert resp2.status_code == 200
    assert b"A valid email address is required." in resp2.data


def test_change_password_success(client, app):
    """POST /profile/password with correct credentials should update password."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password": "brandnewpassword890",
            "confirm_password": "brandnewpassword890",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

    # Check updated hash in DB
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert check_password_hash(user["password_hash"], "brandnewpassword890")
        assert not check_password_hash(user["password_hash"], "password123")

    # Verify flash message
    follow_resp = client.get("/profile")
    assert b"Password updated successfully." in follow_resp.data

    # Verify new password can be used to log in
    client.get("/logout")
    login_resp = client.post(
        "/login",
        data={"email": "nitish@example.com", "password": "brandnewpassword890"},
        follow_redirects=False,
    )
    assert login_resp.status_code == 302
    assert login_resp.headers["Location"] == "/profile"


def test_change_password_wrong_current(client, app):
    """POST /profile/password with incorrect current password should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile/password",
        data={
            "current_password": "wrongcurrentpassword",
            "new_password": "brandnewpassword890",
            "confirm_password": "brandnewpassword890",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Current password is incorrect." in response.data


def test_change_password_mismatch(client, app):
    """POST /profile/password with non-matching confirmation should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password": "brandnewpassword890",
            "confirm_password": "completelydifferent",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"New passwords do not match." in response.data


def test_change_password_short(client, app):
    """POST /profile/password with short password should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password": "short",
            "confirm_password": "short",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"New password must be at least 8 characters long." in response.data


def test_change_password_missing_fields(client, app):
    """POST /profile/password with missing fields should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/profile/password",
        data={
            "current_password": "password123",
            "new_password": "",
            "confirm_password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"All password fields are required." in response.data
