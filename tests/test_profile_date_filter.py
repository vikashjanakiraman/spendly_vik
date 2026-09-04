import pytest
from datetime import date, timedelta
from database.db import get_db, seed_db


@pytest.fixture
def setup_dated_expenses(app):
    """Seed database and insert deterministic dated expenses."""
    with app.app_context():
        seed_db()
        db = get_db()

        # Clear existing seeded expenses to establish predictable baseline
        db.execute("DELETE FROM expenses")

        today = date.today()
        d_today = today.isoformat()
        d_3days = (today - timedelta(days=3)).isoformat()
        d_15days = (today - timedelta(days=15)).isoformat()
        d_45days = (today - timedelta(days=45)).isoformat()
        d_400days = (today - timedelta(days=400)).isoformat()

        # Insert User 1 expenses:
        # Category 1: Food & Dining, Category 2: Groceries
        user1_expenses = [
            (1, 1, "Today Lunch", 250.00, d_today, "Quick meal"),
            (1, 2, "Groceries 3d ago", 1200.00, d_3days, "Weekly stock"),
            (1, 1, "Dining 15d ago", 800.00, d_15days, "Dinner out"),
            (1, 2, "Supermarket 45d ago", 3000.00, d_45days, "Big purchase"),
            (1, 1, "Old Dinner Last Year", 1500.00, d_400days, "Annual party"),
        ]
        for exp in user1_expenses:
            db.execute(
                "INSERT INTO expenses "
                "(user_id, category_id, title, amount, date, notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                exp,
            )

        # Insert User 2 and expenses for strict user isolation verification
        db.execute(
            "INSERT INTO users (id, name, email, password_hash) "
            "VALUES (?, ?, ?, ?)",
            (2, "Second User", "user2@example.com", "hash123"),
        )
        user2_expenses = [
            (2, 1, "User 2 Secret Expense", 9999.00, d_today, "Private"),
            (2, 2, "User 2 Supermarket", 5555.00, d_45days, "Private Grocery"),
        ]
        for exp in user2_expenses:
            db.execute(
                "INSERT INTO expenses "
                "(user_id, category_id, title, amount, date, notes) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                exp,
            )

        db.commit()


# ---------------------------------------------------------------------- #
# 1. DEFAULT ALL-TIME VIEW & AGGREGATIONS
# ---------------------------------------------------------------------- #

def test_profile_date_filter_default_all_time(
    client, app, setup_dated_expenses
):
    """GET /profile without query parameters renders all-time data."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/profile")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Verify active preset pill is 'All Time'
    assert 'class="filter-preset-pill active">All Time</a>' in html
    # Active status badge should not be shown for all-time view
    assert "filter-active-status" not in html
    assert "btn-filter-reset" not in html

    # Verify aggregate stat values:
    # Count: 5, Total: 6,750.00, Avg: 1,350.00, Max: 3,000.00
    assert "6,750.00" in html
    assert "1,350.00" in html
    assert "3,000.00" in html

    # Verify top category is Groceries (4,200.00 > Food & Dining 2,550.00)
    assert "Groceries" in html
    assert "4,200.00" in html
    assert "62.2%" in html
    assert "Food &amp; Dining" in html
    assert "2,550.00" in html
    assert "37.8%" in html

    # Verify recent transaction table rows
    assert "Today Lunch" in html
    assert "Groceries 3d ago" in html
    assert "Dining 15d ago" in html
    assert "Supermarket 45d ago" in html
    assert "Old Dinner Last Year" in html

    # Database state verification
    with app.app_context():
        db = get_db()
        db_count = db.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = 1"
        ).fetchone()[0]
        db_total = db.execute(
            "SELECT SUM(amount) FROM expenses WHERE user_id = 1"
        ).fetchone()[0]
        assert db_count == 5
        assert db_total == 6750.00


def test_profile_date_filter_explicit_all_preset(
    client, app, setup_dated_expenses
):
    """GET /profile?range=all explicitly activates all-time preset view."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/profile?range=all")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert 'class="filter-preset-pill active">All Time</a>' in html
    assert "6,750.00" in html
    assert "filter-active-status" not in html


# ---------------------------------------------------------------------- #
# 2. PRESET FILTERS
# ---------------------------------------------------------------------- #

def test_profile_date_filter_preset_today(
    client, app, setup_dated_expenses
):
    """GET /profile?range=today filters strictly to today's expenses."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    today = date.today()
    response = client.get("/profile?range=today")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Template active pill and badge
    assert 'class="filter-preset-pill active">Today</a>' in html
    assert "filter-active-status" in html
    assert f"Today ({today.strftime('%b %d, %Y')})" in html
    assert "✕ Clear filter" in html
    assert "btn-filter-reset" in html

    # Stats: Total 250.00, Count 1, Avg 250.00, Max 250.00
    assert "Today Lunch" in html
    assert "250.00" in html

    # Excluded expenses
    assert "Groceries 3d ago" not in html
    assert "Dining 15d ago" not in html
    assert "Supermarket 45d ago" not in html
    assert "Old Dinner Last Year" not in html


def test_profile_date_filter_preset_last7(
    client, app, setup_dated_expenses
):
    """GET /profile?range=last7 returns expenses within past 7 days."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/profile?range=last7")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Active pill and badge
    assert 'class="filter-preset-pill active">Last 7 Days</a>' in html
    assert "Showing data for <strong>Last 7 Days" in html

    # Expected: Today Lunch (250) + Groceries 3d ago (1200) = 1,450.00
    assert "1,450.00" in html
    assert "Today Lunch" in html
    assert "Groceries 3d ago" in html

    # Excluded
    assert "Dining 15d ago" not in html
    assert "Supermarket 45d ago" not in html
    assert "Old Dinner Last Year" not in html


def test_profile_date_filter_preset_last30(
    client, app, setup_dated_expenses
):
    """GET /profile?range=last30 returns expenses within past 30 days."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/profile?range=last30")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Active pill and badge
    assert 'class="filter-preset-pill active">Last 30 Days</a>' in html
    assert "Showing data for <strong>Last 30 Days" in html

    # Expected: 250 + 1200 + 800 = 2,250.00
    assert "2,250.00" in html
    assert "Today Lunch" in html
    assert "Groceries 3d ago" in html
    assert "Dining 15d ago" in html

    # Excluded
    assert "Supermarket 45d ago" not in html
    assert "Old Dinner Last Year" not in html


def test_profile_date_filter_preset_this_month(
    client, app, setup_dated_expenses
):
    """GET /profile?range=this_month matches expenses in current month."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    today = date.today()
    start_of_month = date(today.year, today.month, 1).isoformat()

    response = client.get("/profile?range=this_month")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    assert 'class="filter-preset-pill active">This Month</a>' in html
    assert "Showing data for <strong>This Month" in html

    with app.app_context():
        db = get_db()
        month_rows = db.execute(
            "SELECT title, amount FROM expenses "
            "WHERE user_id = 1 AND date >= ? AND date <= ?",
            (start_of_month, today.isoformat()),
        ).fetchall()
        month_total = sum(r["amount"] for r in month_rows)
        month_titles = [r["title"] for r in month_rows]

    formatted_total = f"{month_total:,.2f}"
    assert formatted_total in html
    for title in month_titles:
        assert title in html

    # Old Dinner Last Year (400 days ago) is never in this month
    assert "Old Dinner Last Year" not in html


def test_profile_date_filter_preset_this_year(
    client, app, setup_dated_expenses
):
    """GET /profile?range=this_year matches current year expenses."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    today = date.today()
    start_of_year = date(today.year, 1, 1).isoformat()

    response = client.get("/profile?range=this_year")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    assert 'class="filter-preset-pill active">This Year</a>' in html
    assert "Showing data for <strong>This Year" in html
    assert "Today Lunch" in html

    # Old Dinner Last Year (400 days ago) is strictly excluded
    assert "Old Dinner Last Year" not in html

    with app.app_context():
        db = get_db()
        year_total = db.execute(
            "SELECT COALESCE(SUM(amount), 0.0) FROM expenses "
            "WHERE user_id = 1 AND date >= ? AND date <= ?",
            (start_of_year, today.isoformat()),
        ).fetchone()[0]
    assert f"{year_total:,.2f}" in html


# ---------------------------------------------------------------------- #
# 3. CUSTOM DATE RANGES
# ---------------------------------------------------------------------- #

def test_profile_date_filter_custom_range_both_dates(
    client, app, setup_dated_expenses
):
    """GET /profile with start_date & end_date filters inclusively."""
    today = date.today()
    start_d = (today - timedelta(days=20)).isoformat()
    end_d = (today - timedelta(days=2)).isoformat()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    url = f"/profile?range=custom&start_date={start_d}&end_date={end_d}"
    response = client.get(url)
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Form inputs should preserve the requested filter values
    assert f'value="{start_d}"' in html
    assert f'value="{end_d}"' in html

    # Filter status badge should display formatted range
    assert "Showing data for <strong>Custom (" in html

    # Expected: Groceries 3d ago (1200) + Dining 15d ago (800) = 2,000.00
    assert "2,000.00" in html
    assert "Groceries 3d ago" in html
    assert "Dining 15d ago" in html

    # Excluded
    assert "Today Lunch" not in html
    assert "Supermarket 45d ago" not in html
    assert "Old Dinner Last Year" not in html


def test_profile_date_filter_custom_swapped_dates(
    client, app, setup_dated_expenses
):
    """When start_date > end_date, app auto-swaps and filters properly."""
    today = date.today()
    earlier = (today - timedelta(days=20)).isoformat()
    later = (today - timedelta(days=2)).isoformat()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # Pass later date as start_date, and earlier date as end_date
    url = f"/profile?range=custom&start_date={later}&end_date={earlier}"
    response = client.get(url)
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Should still correctly capture the 20d to 2d window
    assert "2,000.00" in html
    assert "Groceries 3d ago" in html
    assert "Dining 15d ago" in html
    assert "Today Lunch" not in html


def test_profile_date_filter_custom_start_date_only(
    client, app, setup_dated_expenses
):
    """Specifying only start_date filters from that date onwards."""
    today = date.today()
    start_d = (today - timedelta(days=5)).isoformat()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get(f"/profile?start_date={start_d}")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Filter label check
    assert "onwards" in html
    assert f'value="{start_d}"' in html

    # Expected: Today Lunch (250) + Groceries 3d ago (1200) = 1,450.00
    assert "1,450.00" in html
    assert "Today Lunch" in html
    assert "Groceries 3d ago" in html
    assert "Dining 15d ago" not in html


def test_profile_date_filter_custom_end_date_only(
    client, app, setup_dated_expenses
):
    """Specifying only end_date filters up to that date."""
    today = date.today()
    end_d = (today - timedelta(days=30)).isoformat()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get(f"/profile?end_date={end_d}")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Filter label check
    assert "Up to" in html
    assert f'value="{end_d}"' in html

    # Expected: Supermarket 45d ago (3000) + Old Dinner Last Year (1500)
    assert "4,500.00" in html
    assert "Supermarket 45d ago" in html
    assert "Old Dinner Last Year" in html
    assert "Today Lunch" not in html


# ---------------------------------------------------------------------- #
# 4. EDGE CASES & ROBUSTNESS
# ---------------------------------------------------------------------- #

def test_profile_date_filter_invalid_dates_fallback(
    client, app, setup_dated_expenses
):
    """Invalid date strings fallback safely to all-time view."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # Both invalid dates
    url = "/profile?range=custom&start_date=not-a-date&end_date=2026-99-99"
    response = client.get(url)
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert 'class="filter-preset-pill active">All Time</a>' in html
    assert "6,750.00" in html


def test_profile_date_filter_one_invalid_one_valid_date(
    client, app, setup_dated_expenses
):
    """One valid and one invalid date filters using valid boundary."""
    today = date.today()
    start_d = (today - timedelta(days=5)).isoformat()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # Valid start date, invalid end date
    url = f"/profile?range=custom&start_date={start_d}&end_date=invalid_date"
    response = client.get(url)
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert "onwards" in html
    assert "1,450.00" in html
    assert "Today Lunch" in html
    assert "Groceries 3d ago" in html
    assert "Dining 15d ago" not in html


def test_profile_date_filter_whitespace_handling(
    client, app, setup_dated_expenses
):
    """Query parameters containing surrounding whitespace are trimmed."""
    today = date.today()
    start_d = (today - timedelta(days=5)).isoformat()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # Preset with spaces
    resp1 = client.get("/profile?range=%20%20today%20%20")
    assert resp1.status_code == 200
    assert 'class="filter-preset-pill active">Today</a>' in (
        resp1.data.decode("utf-8")
    )

    # Custom date with spaces
    resp2 = client.get(
        f"/profile?range=%20custom%20&start_date=%20{start_d}%20"
    )
    assert resp2.status_code == 200
    assert "1,450.00" in resp2.data.decode("utf-8")


def test_profile_date_filter_unknown_preset_fallback(
    client, app, setup_dated_expenses
):
    """Unknown preset parameter safely defaults to all-time view."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get("/profile?range=non_existent_preset_xyz")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert 'class="filter-preset-pill active">All Time</a>' in html
    assert "6,750.00" in html


def test_profile_date_filter_empty_state(
    client, app, setup_dated_expenses
):
    """Non-matching date ranges render proper empty states."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # Range in past with no expenses
    url = "/profile?range=custom&start_date=1995-01-01&end_date=1995-01-31"
    response = client.get(url)
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Zeroed metrics
    assert "₹0.00" in html
    assert "None yet" in html

    # Empty state messages
    assert "No expenses recorded for the selected timeframe." in html
    assert "No category data for this timeframe." in html
    assert "View All Time" in html


# ---------------------------------------------------------------------- #
# 5. USER ISOLATION
# ---------------------------------------------------------------------- #

def test_profile_date_filter_user_isolation_user1(
    client, app, setup_dated_expenses
):
    """User 1 queries must never leak or aggregate User 2's data."""
    today = date.today().isoformat()

    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    # All-time view isolation
    resp_all = client.get("/profile")
    html_all = resp_all.data.decode("utf-8")
    assert "User 2 Secret Expense" not in html_all
    assert "User 2 Supermarket" not in html_all
    assert "9,999.00" not in html_all
    assert "5,555.00" not in html_all

    # Filtered view isolation
    url = f"/profile?range=custom&start_date={today}&end_date={today}"
    resp_today = client.get(url)
    html_today = resp_today.data.decode("utf-8")
    assert "User 2 Secret Expense" not in html_today
    assert "9,999.00" not in html_today
    assert "250.00" in html_today


def test_profile_date_filter_user_isolation_user2(
    client, app, setup_dated_expenses
):
    """User 2 queries only return User 2 expenses and never leak User 1."""
    with client.session_transaction() as session:
        session["user_id"] = 2
        session["user_name"] = "Second User"

    # User 2 all-time view: Total = 9999 + 5555 = 15,554.00, count = 2
    response = client.get("/profile")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert "15,554.00" in html
    assert "User 2 Secret Expense" in html
    assert "User 2 Supermarket" in html

    # User 1 expenses must not appear
    assert "Today Lunch" not in html
    assert "Groceries 3d ago" not in html
    assert "Dining 15d ago" not in html
    assert "Supermarket 45d ago" not in html
    assert "Old Dinner Last Year" not in html

    # User 2 today filter: only 9,999.00
    resp_today = client.get("/profile?range=today")
    html_today = resp_today.data.decode("utf-8")
    assert "9,999.00" in html_today
    assert "User 2 Secret Expense" in html_today
    assert "User 2 Supermarket" not in html_today


# ---------------------------------------------------------------------- #
# 6. TEMPLATE & UI ELEMENTS ASSERTIONS
# ---------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "range_param,expected_active_text",
    [
        ("all", "All Time"),
        ("today", "Today"),
        ("last7", "Last 7 Days"),
        ("this_month", "This Month"),
        ("last30", "Last 30 Days"),
        ("this_year", "This Year"),
    ],
)
def test_profile_date_filter_active_pills_rendering(
    client, app, setup_dated_expenses, range_param, expected_active_text
):
    """Each preset marks its corresponding pill active and unmarks others."""
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Nitish Kumar"

    response = client.get(f"/profile?range={range_param}")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    # Verify expected active pill
    active_snippet = (
        f'class="filter-preset-pill active">{expected_active_text}</a>'
    )
    assert active_snippet in html

    # Verify other pills do not have the active class
    all_presets = [
        "All Time",
        "Today",
        "Last 7 Days",
        "This Month",
        "Last 30 Days",
        "This Year",
    ]
    for preset in all_presets:
        if preset != expected_active_text:
            other_snippet = f'class="filter-preset-pill active">{preset}</a>'
            assert other_snippet not in html
