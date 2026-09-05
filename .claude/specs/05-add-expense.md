# Spec: Add Expense

## Overview
The Add Expense feature allows authenticated Spendly users to record new financial transactions with essential details including a title/description, amount (in ₹ INR), category (selected from predefined categories), transaction date, and optional notes. Adding expenses directly updates the user's spending records, dashboard analytics, category breakdowns, and recent transaction history, serving as the core data input mechanism for Spendly.

## Depends on
- Step 1: Database Setup (`database/db.py`, `expenses`, `categories`, and `users` tables)
- Step 2: Registration (User account creation)
- Step 3: Login & Logout (Session management and `@login_required` decorator)
- Step 4: User Profile (Transaction summary, stats, and profile overview)

## Routes
- `GET /expenses/add` — Display the expense creation form with categories dropdown and default current date — logged-in
- `POST /expenses/add` — Validate input data, insert new expense record linked to session `user_id`, and redirect to profile — logged-in

## Database changes
No database changes.
(The existing `expenses` table schema in `database/db.py` already includes `id`, `user_id`, `category_id`, `title`, `amount`, `date`, `notes`, and `created_at` with appropriate foreign keys.)

## Templates
- **Create:**
  - `templates/add_expense.html` — Add expense form extending `base.html` containing title, amount, category select (with emojis/icons), date picker (defaulting to today), optional notes textarea, submit button, and cancel link.
- **Modify:**
  - `templates/profile.html` — Add a prominent "+ Add Expense" action button in the profile header/transaction toolbar linking to `/expenses/add`.
  - `templates/base.html` — Include "+ Add Expense" quick action link in navigation bar when a user is authenticated.

## Files to change
- `app.py` — Replace placeholder `add_expense()` route with full `GET` and `POST` handlers, input validation (title, positive numeric amount, category existence, date format), parameterized database insertion, flash messaging, and redirection to profile.
- `templates/profile.html` — Add "+ Add Expense" button linking to `/expenses/add`.
- `templates/base.html` — Add quick "+ Add Expense" link in navigation bar for logged-in users.
- `static/css/style.css` — Add responsive form styling, input groupings with currency prefix, custom select controls, and button layouts for expense creation.

## Files to create
- `.claude/specs/05-add-expense.md` — Feature specification document.
- `templates/add_expense.html` — Expense creation form template extending `base.html`.
- `tests/test_add_expense.py` — Comprehensive unit and integration test suite covering route access, form rendering, valid submissions, input validation errors, and user data isolation.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Protect routes: `@login_required` decorator on `/expenses/add` (redirect unauthenticated users to `/login`)
- Associate newly created expenses strictly with `session["user_id"]`
- Validate form fields server-side:
  - `title`: required, non-empty string (max 100 characters)
  - `amount`: required, valid positive float (> 0)
  - `category_id`: required, must correspond to a valid category in `categories` table
  - `date`: required, valid `YYYY-MM-DD` date format (default to today `date.today().isoformat()`)
  - `notes`: optional text
- Render helpful, contextual error messages inline or in an alert banner if validation fails without clearing valid input values
- On successful insertion, commit to database, flash success message, and redirect to `url_for("profile")`

## Definition of done
- [ ] Navigating to `GET /expenses/add` when logged out redirects to `/login`.
- [ ] Navigating to `GET /expenses/add` when logged in renders the "Add Expense" form extending `base.html`.
- [ ] Category dropdown in the form is dynamically populated from the `categories` table in the database with names and icons.
- [ ] Date input defaults to today's date in `YYYY-MM-DD` format.
- [ ] Submitting valid data (`title`, `amount`, `category_id`, `date`, `notes`) inserts a new row into `expenses` linked to `session["user_id"]` and redirects to `/profile`.
- [ ] Submitting invalid inputs (empty title, non-positive or non-numeric amount, invalid date, nonexistent category) displays clear error messages on the form and does not crash or insert records.
- [ ] The newly added expense immediately appears in the recent transactions table and updates summary stats (Total Spent, Total Count, Average per Expense, Category Breakdown) on `/profile`.
- [ ] Users cannot create expenses on behalf of other users; all created expenses are assigned to the authenticated user's ID.
- [ ] "+ Add Expense" action button on `/profile` and navigation bar links correctly to `/expenses/add`.
- [ ] All automated tests in `tests/test_add_expense.py` pass with `pytest`.
