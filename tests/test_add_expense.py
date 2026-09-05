import pytest
from database.db import seed_db, get_db


def test_add_expense_requires_login(client):
    """Unauthenticated users must be redirected to /login on GET and POST."""
    response_get = client.get("/expenses/add", follow_redirects=False)
    assert response_get.status_code == 302
    assert "/login" in response_get.headers.get("Location", "")

    response_post = client.post(
        "/expenses/add",
        data={
            "title": "Unauthorized Expense",
            "amount": "100",
            "category_id": "1",
            "date": "2026-09-05",
        },
        follow_redirects=False,
    )
    assert response_post.status_code == 302
    assert "/login" in response_post.headers.get("Location", "")


def test_add_expense_page_renders(client, app):
    """Authenticated user can load the Add Expense page with categories and default date."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/expenses/add")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Add New Expense" in text
    assert "Expense Title / Description" in text
    assert "Amount (₹)" in text
    assert "Food &amp; Dining" in text or "Food & Dining" in text
    assert "Groceries" in text
    assert "Transportation" in text
    assert "Save Expense" in text


def test_add_expense_success(client, app):
    """POST /expenses/add with valid payload creates a new expense and redirects to /profile."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/expenses/add",
        data={
            "title": "Swiggy Weekend Lunch",
            "amount": "450.75",
            "category_id": "1",
            "date": "2026-09-05",
            "notes": "Ordered South Indian combo with cold beverage",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Expense added successfully!" in text
    assert "Swiggy Weekend Lunch" in text
    assert "450.75" in text

    # Verify directly in the database
    with app.app_context():
        db = get_db()
        exp = db.execute(
            "SELECT * FROM expenses WHERE title = ? AND user_id = 1",
            ("Swiggy Weekend Lunch",),
        ).fetchone()
        assert exp is not None
        assert exp["amount"] == 450.75
        assert exp["category_id"] == 1
        assert exp["date"] == "2026-09-05"
        assert exp["notes"] == "Ordered South Indian combo with cold beverage"


def test_add_expense_empty_or_whitespace_title(client, app):
    """POST /expenses/add with missing/empty title should show validation error."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post(
        "/expenses/add",
        data={
            "title": "   ",
            "amount": "250.00",
            "category_id": "1",
            "date": "2026-09-05",
        },
    )

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Expense title is required." in text

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(*) as c FROM expenses WHERE amount = 250.00").fetchone()["c"]
        assert count == 0


def test_add_expense_title_too_long(client, app):
    """POST /expenses/add with title > 100 chars should show error."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1

    long_title = "A" * 105
    response = client.post(
        "/expenses/add",
        data={
            "title": long_title,
            "amount": "150.00",
            "category_id": "1",
            "date": "2026-09-05",
        },
    )

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Expense title cannot exceed 100 characters." in text


def test_add_expense_invalid_amounts(client, app):
    """POST /expenses/add with zero, negative, empty, or non-numeric amount should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1

    # Empty amount
    r_empty = client.post(
        "/expenses/add",
        data={"title": "Coffee", "amount": "", "category_id": "1", "date": "2026-09-05"},
    )
    assert "Expense amount is required." in r_empty.get_data(as_text=True)

    # Zero amount
    r_zero = client.post(
        "/expenses/add",
        data={"title": "Coffee", "amount": "0", "category_id": "1", "date": "2026-09-05"},
    )
    assert "Amount must be greater than zero." in r_zero.get_data(as_text=True)

    # Negative amount
    r_neg = client.post(
        "/expenses/add",
        data={"title": "Coffee", "amount": "-150.00", "category_id": "1", "date": "2026-09-05"},
    )
    assert "Amount must be greater than zero." in r_neg.get_data(as_text=True)

    # Non-numeric string amount
    r_str = client.post(
        "/expenses/add",
        data={"title": "Coffee", "amount": "not_a_number", "category_id": "1", "date": "2026-09-05"},
    )
    assert "Please enter a valid positive number for amount." in r_str.get_data(as_text=True)


def test_add_expense_invalid_date(client, app):
    """POST /expenses/add with missing or malformed date should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1

    # Missing date
    r_nodate = client.post(
        "/expenses/add",
        data={"title": "Metro", "amount": "50", "category_id": "1", "date": ""},
    )
    assert "Transaction date is required." in r_nodate.get_data(as_text=True)

    # Malformed date
    r_bad = client.post(
        "/expenses/add",
        data={"title": "Metro", "amount": "50", "category_id": "1", "date": "05/09/2026"},
    )
    assert "Please enter a valid date in YYYY-MM-DD format." in r_bad.get_data(as_text=True)


def test_add_expense_invalid_category(client, app):
    """POST /expenses/add with nonexistent or invalid category should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1

    # Missing category
    r_nocat = client.post(
        "/expenses/add",
        data={"title": "Medicines", "amount": "300", "category_id": "", "date": "2026-09-05"},
    )
    assert "Please select an expense category." in r_nocat.get_data(as_text=True)

    # Nonexistent category ID
    r_fakecat = client.post(
        "/expenses/add",
        data={"title": "Medicines", "amount": "300", "category_id": "9999", "date": "2026-09-05"},
    )
    assert "Selected category does not exist." in r_fakecat.get_data(as_text=True)

    # Non-numeric category ID
    r_invalidcat = client.post(
        "/expenses/add",
        data={"title": "Medicines", "amount": "300", "category_id": "unknown", "date": "2026-09-05"},
    )
    assert "Selected category is invalid." in r_invalidcat.get_data(as_text=True)


def test_add_expense_notes_too_long(client, app):
    """POST /expenses/add with notes > 500 chars should fail."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1

    long_notes = "N" * 505
    response = client.post(
        "/expenses/add",
        data={
            "title": "Shopping",
            "amount": "500",
            "category_id": "1",
            "date": "2026-09-05",
            "notes": long_notes,
        },
    )
    assert response.status_code == 200
    assert "Notes cannot exceed 500 characters." in response.get_data(as_text=True)


def test_add_expense_preserves_form_values_on_error(client, app):
    """When validation fails, other valid inputs must remain populated in the form."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post(
        "/expenses/add",
        data={
            "title": "Preserved Dinner Title",
            "amount": "-500",  # Invalid amount
            "category_id": "2",
            "date": "2026-09-05",
            "notes": "Preserved Notes Content",
        },
    )

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Amount must be greater than zero." in text
    assert "Preserved Dinner Title" in text
    assert "Preserved Notes Content" in text
    assert "2026-09-05" in text


def test_add_expense_user_isolation(client, app):
    """Expenses added by User 1 should not belong to or show up on User 2."""
    with app.app_context():
        seed_db()
        db = get_db()
        # Create second user
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Priya Sharma", "priya@example.com", "hash123"),
        )
        db.commit()
        priya_id = db.execute("SELECT id FROM users WHERE email = 'priya@example.com'").fetchone()["id"]

    # User 1 adds an expense
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    client.post(
        "/expenses/add",
        data={
            "title": "Nitish Exclusive Expense",
            "amount": "777.00",
            "category_id": "1",
            "date": "2026-09-05",
        },
    )

    # Log in as User 2 (Priya)
    with client.session_transaction() as session:
        session["user_id"] = priya_id
        session["user_name"] = "Priya Sharma"

    # Priya's profile should not show Nitish's expense
    response = client.get("/profile")
    assert response.status_code == 200
    assert "Nitish Exclusive Expense" not in response.get_data(as_text=True)

    # Check DB directly
    with app.app_context():
        db = get_db()
        priya_expenses = db.execute("SELECT * FROM expenses WHERE user_id = ?", (priya_id,)).fetchall()
        assert len(priya_expenses) == 0


def test_add_expense_updates_dashboard_metrics(client, app):
    """Adding expenses updates the summary totals and category breakdown accurately."""
    with app.app_context():
        seed_db()
        db = get_db()
        # Create new fresh user with 0 expenses
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Ananya Rao", "ananya@example.com", "hash123"),
        )
        db.commit()
        user_id = db.execute("SELECT id FROM users WHERE email = 'ananya@example.com'").fetchone()["id"]

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["user_name"] = "Ananya Rao"

    # Initially 0
    resp1 = client.get("/profile")
    assert "0.00" in resp1.get_data(as_text=True)

    # Add 1st expense: 350.00 in Transportation (category 3)
    client.post(
        "/expenses/add",
        data={
            "title": "Metro Recharge",
            "amount": "350.00",
            "category_id": "3",
            "date": "2026-09-05",
        },
    )

    # Add 2nd expense: 650.00 in Groceries (category 2)
    client.post(
        "/expenses/add",
        data={
            "title": "Weekly Vegetables",
            "amount": "650.00",
            "category_id": "2",
            "date": "2026-09-05",
        },
    )

    resp2 = client.get("/profile")
    assert resp2.status_code == 200
    text = resp2.get_data(as_text=True)
    # Total spent: 350 + 650 = 1,000.00
    assert "1,000.00" in text
    assert "Metro Recharge" in text
    assert "Weekly Vegetables" in text
