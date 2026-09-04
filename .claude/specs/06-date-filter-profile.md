# Spec: Date Filter for Profile Page

## Overview
The Date Filter feature for the Profile Page allows Spendly users to filter their financial transaction summary, category breakdowns, and expense history by specific timeframes. Users can select quick preset filters (e.g., "This Month", "Last 7 Days", "Last 30 Days", "This Year", "All Time") or specify custom start and end dates. Applying a date filter dynamically recalculates summary metrics (Total Spent, Total Count, Average per Expense, Top Category) and restricts the category progress breakdown and transaction table to the chosen timeframe, empowering users to analyze spending across distinct budgeting periods.

## Depends on
- Step 1: Database Setup (`database/db.py`, `expenses` & `categories` tables)
- Step 2: Registration (User account creation)
- Step 3: Login & Logout (Session management and protected routes)
- Step 4: User Profile (Dashboard stats, category breakdown, account settings)

## Routes
- `GET /profile` — Updated route handler accepting optional query parameters (`start_date`, `end_date`, `range`, `tab`) — logged-in

If no new routes: No new routes.

## Database changes
No database changes.
(The existing `expenses` table `date` column is queried using parameterized SQL date comparisons: `e.date >= ? AND e.date <= ?`.)

## Templates
- **Create:** No new templates.
- **Modify:**
  - `templates/profile.html` — Add a date filter toolbar to the "Transaction Summary" tab featuring preset buttons (Today, Last 7 Days, This Month, Last 30 Days, This Year, All Time), start/end date inputs, Apply and Reset buttons, active filter indicators, and empty-state messaging when no transactions match the timeframe.

## Files to change
- `app.py` — Update the `profile()` route handler to extract and sanitize date query parameters, calculate date boundaries for presets, construct parameterized SQL queries for stats, top category, category breakdown, and recent expenses, and pass active filter state to the template.
- `templates/profile.html` — Add the date filter controls bar, bind preset and custom date form inputs, display active range summaries, and ensure tab switching preserves filter query parameters.
- `static/css/style.css` — Add responsive styling for the filter controls toolbar, preset pills, custom date input fields, submit/reset action buttons, and active filter badge indicators.

## Files to create
- `.claude/specs/06-date-filter-profile.md` — Feature specification document.
- `tests/test_profile_date_filter.py` — Comprehensive unit and integration test suite covering default view, preset filters, custom date ranges, boundary dates, invalid date inputs, and user data isolation.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never string-format dates directly into SQL statements
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Protect routes: ensure unauthenticated requests to `/profile` redirect to `/login`
- Scope all filtered queries with `WHERE user_id = ?` to prevent cross-user data leakage (IDOR prevention)
- Sanitize and validate date inputs gracefully (`YYYY-MM-DD` format); fallback safely to default all-time view if invalid formats or contradictory ranges (start > end) are supplied
- Ensure all 4 dashboard widgets dynamically synchronize with the active date filter:
  1. Stat Summary Cards (Total Spent, Total Count, Top Category, Average / Expense)
  2. Spending by Category Progress Breakdown
  3. Expense Insights (Highest Expense in period, Active Categories in period)
  4. Recent Transactions Table

## Definition of done
- [ ] Navigating to `GET /profile` without query parameters displays all-time expenses and stats by default.
- [ ] Selecting quick preset filters ("Last 7 Days", "This Month", "Last 30 Days", "This Year", "All Time") accurately recalculates summary stats, category breakdown, and transaction history for that period.
- [ ] Submitting custom `start_date` and `end_date` inputs correctly limits dashboard data to expenses within that inclusive date range.
- [ ] Supplying only `start_date` filters expenses from that date onward; supplying only `end_date` filters expenses up to that date.
- [ ] Clicking "Reset" or "All Time" clears active filters and restores full transaction overview.
- [ ] Submitting invalid date formats or malformed query strings handles gracefully without raising 500 errors.
- [ ] If no expenses exist within the selected timeframe, clean empty states are rendered for stats, category breakdown, and transaction table.
- [ ] Switching between "Transaction Summary" and "Account Settings" tabs preserves active date filter query parameters in the URL.
- [ ] All automated tests in `tests/test_profile_date_filter.py` pass with `pytest`.
