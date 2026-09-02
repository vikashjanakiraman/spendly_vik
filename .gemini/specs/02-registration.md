# Spec: Registration

## Overview
User registration provides an onboarding entry point for new users to create an account in Spendly. It ensures secure account creation by validating credentials, enforcing unique email constraints, and hashing passwords using Werkzeug before storing user records in SQLite.

## Depends on
Step 1: Database Setup (`database/db.py`, `users` table).

## Routes
- `GET /register` — Displays the user registration form — public
- `POST /register` — Validates form data, hashes the password, creates a new user record in the database, and redirects to `/login` or re-renders form with error messages — public

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:** `templates/register.html` — Ensure the form submits `name`, `email`, and `password` via `POST /register`, displays server validation/duplicate errors using `auth-error`, and retains previously entered `name` and `email` on error.

## Files to change
- `app.py` — Implement `GET` and `POST` handlers on `/register`, including request parsing, validation, database query to check existing email, password hashing with `generate_password_hash`, parameterized user insertion, and redirection.
- `templates/register.html` — Update form inputs to preserve entered values (`name`, `email`) on validation failure.

## Files to create
- `tests/test_register.py` — Automated tests covering successful registration, validation failures (missing fields, short passwords), duplicate email handling, and password hashing verification.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate that `name`, `email`, and `password` are present and non-empty.
- Enforce password length minimum (at least 8 characters).
- Check for existing email in `users` table and return a clear user-friendly error message (e.g., "An account with this email already exists.").
- Never store or log plain-text passwords.

## Definition of done
- [ ] Navigating to `GET /register` renders the registration form extending `base.html`.
- [ ] Submitting empty required fields displays an appropriate validation error message.
- [ ] Submitting a password shorter than 8 characters displays a validation error message.
- [ ] Submitting an already registered email displays a user-friendly error message ("An account with this email already exists.").
- [ ] Submitting valid data inserts a new record into `users` table with password hashed using `werkzeug.security.generate_password_hash`.
- [ ] Successful registration redirects the user to `/login`.
- [ ] Preserves `name` and `email` values in the form when rendering an error so the user does not have to retype them.
- [ ] All database queries use parameterized SQL.
- [ ] All test cases in `tests/test_register.py` pass.
