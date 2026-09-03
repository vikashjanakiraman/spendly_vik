import pytest
from database.db import seed_db, get_db


def test_pricing_page_public(client):
    """GET /pricing should be publicly accessible and display plans."""
    response = client.get("/pricing")
    assert response.status_code == 200
    assert b"Spendly Starter" in response.data
    assert b"Spendly Pro (Monthly)" in response.data
    assert b"Spendly Pro (Annual)" in response.data
    assert b"199" in response.data
    assert b"1,499" in response.data


def test_pricing_page_authenticated_free_user(client, app):
    """Authenticated user on free tier should see Current Plan indicator on Starter."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/pricing")
    assert response.status_code == 200
    assert b"Current Plan" in response.data


def test_checkout_unauthenticated_redirect(client):
    """Unauthenticated access to checkout should redirect to /login."""
    resp_get = client.get("/checkout/monthly", follow_redirects=False)
    assert resp_get.status_code == 302
    assert "/login" in resp_get.headers["Location"]

    resp_post = client.post("/checkout/monthly", data={"payment_method": "card"}, follow_redirects=False)
    assert resp_post.status_code == 302
    assert "/login" in resp_post.headers["Location"]


def test_checkout_invalid_plan(client, app):
    """Navigating to checkout with invalid plan ID should redirect to /pricing."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/checkout/nonexistent_plan", follow_redirects=False)
    assert response.status_code == 302
    assert "/pricing" in response.headers["Location"]


def test_checkout_page_authenticated(client, app):
    """GET /checkout/<plan_id> should render order summary and payment form."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/checkout/monthly")
    assert response.status_code == 200
    assert b"Spendly Pro (Monthly)" in response.data
    assert b"199.00" in response.data
    assert b"Payment Details" in response.data


def test_checkout_card_success(client, app):
    """POST /checkout/monthly with valid card details should create subscription and redirect."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/checkout/monthly",
        data={
            "payment_method": "card",
            "card_name": "Nitish Kumar",
            "card_number": "4532 0150 9988 1234",
            "card_exp": "12/28",
            "card_cvv": "789",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/payment/success"

    with app.app_context():
        db = get_db()
        sub = db.execute("SELECT * FROM subscriptions WHERE user_id = 1").fetchone()
        assert sub is not None
        assert sub["plan_id"] == "monthly"
        assert sub["amount"] == 199.0
        assert "Card ending in 1234" in sub["payment_method"]
        assert sub["status"] == "active"


def test_checkout_card_validation_errors(client, app):
    """Card payment validation should catch missing/malformed fields."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # Missing card name
    r1 = client.post("/checkout/monthly", data={
        "payment_method": "card",
        "card_name": "",
        "card_number": "4532111122223333",
        "card_exp": "12/28",
        "card_cvv": "123",
    })
    assert r1.status_code == 200
    assert b"Name on card is required." in r1.data

    # Invalid card number
    r2 = client.post("/checkout/monthly", data={
        "payment_method": "card",
        "card_name": "Nitish",
        "card_number": "1234",
        "card_exp": "12/28",
        "card_cvv": "123",
    })
    assert r2.status_code == 200
    assert b"Please enter a valid card number" in r2.data

    # Invalid expiry format
    r3 = client.post("/checkout/monthly", data={
        "payment_method": "card",
        "card_name": "Nitish",
        "card_number": "4532111122223333",
        "card_exp": "2028-12",
        "card_cvv": "123",
    })
    assert r3.status_code == 200
    assert b"Please enter expiration date in MM/YY format." in r3.data

    # Invalid CVV
    r4 = client.post("/checkout/monthly", data={
        "payment_method": "card",
        "card_name": "Nitish",
        "card_number": "4532111122223333",
        "card_exp": "12/28",
        "card_cvv": "1",
    })
    assert r4.status_code == 200
    assert b"Please enter a valid 3 or 4 digit CVV." in r4.data


def test_checkout_upi_success(client, app):
    """POST /checkout/annual with valid UPI ID should activate Pro Annual plan."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/checkout/annual",
        data={
            "payment_method": "upi",
            "upi_id": "nitish@okaxis",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/payment/success"

    with app.app_context():
        db = get_db()
        sub = db.execute("SELECT * FROM subscriptions WHERE user_id = 1 AND plan_id = 'annual'").fetchone()
        assert sub is not None
        assert sub["amount"] == 1499.0
        assert "UPI (nitish@okaxis)" in sub["payment_method"]


def test_checkout_upi_invalid(client, app):
    """POST /checkout with invalid UPI ID should fail validation."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.post(
        "/checkout/annual",
        data={
            "payment_method": "upi",
            "upi_id": "invalidupi",
        },
    )

    assert response.status_code == 200
    assert b"Please enter a valid UPI ID" in response.data


def test_payment_success_page(client, app):
    """GET /payment/success should display receipt when user has active subscription."""
    with app.app_context():
        seed_db()
        db = get_db()
        db.execute(
            "INSERT INTO subscriptions (user_id, plan_id, amount, payment_method, status) VALUES (1, 'annual', 1499.0, 'UPI (nitish@okaxis)', 'active')"
        )
        db.commit()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/payment/success")
    assert response.status_code == 200
    assert b"Payment Successful!" in response.data
    assert b"Spendly Pro (Annual)" in response.data
    assert b"1,499.00" in response.data
    assert b"Transaction Receipt" in response.data


def test_payment_success_no_subscription_redirect(client, app):
    """GET /payment/success without any active subscription redirects to /pricing."""
    with app.app_context():
        seed_db()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/payment/success", follow_redirects=False)
    assert response.status_code == 302
    assert "/pricing" in response.headers["Location"]


def test_profile_displays_active_subscription(client, app):
    """Profile page should display Pro badge when user has active subscription."""
    with app.app_context():
        seed_db()
        db = get_db()
        db.execute(
            "INSERT INTO subscriptions (user_id, plan_id, amount, payment_method, status) VALUES (1, 'monthly', 199.0, 'Card ending in 1234', 'active')"
        )
        db.commit()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Spendly Pro (Monthly)" in response.data
