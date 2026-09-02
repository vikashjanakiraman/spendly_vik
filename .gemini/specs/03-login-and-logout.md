# Spec: Login and Logout

## Overview
User authentication provides secure login and session management for Spendly. It verifies user credentials against the SQLite database using `check_password_hash`, initializes the user session upon successful login, dynamically adapts navigation for logged-in users, and enables users to securely log out by clearing their active session.

## Depends on
- Step 1: Database Setup (`database/db.py`, `users` table)
- Step 2: Registration (`app.py`, password hashing with Werkzeug)

## Routes
- `GET /login` — Displays login form — public
- `POST /login` — Authenticates credentials, creates session, and redirects to `/profile` or renders error — public
- `GET /logout` — Clears active user session and redirects to `/login` — public/logged-in

## Database changes
No database changes.

## Templates
- **Create:** None
- **Modify:**
  - `templates/login.html` — Update form action to `{{ url_for('login') }}`, display server errors, and retain `email` value on failed attempts.
  - `templates/base.html` — Conditionally render nav links based on `session.get('user_id')` (showing Profile and Sign out when authenticated; Sign in and Get started when logged out).

## Files to change
- `app.py` — Implement `GET` and `POST` handlers on `/login`, implement `/logout`, manage `session['user_id']` and `session['user_name']`, and verify password hash with `check_password_hash`.
- `templates/login.html` — Retain entered email on error and use dynamic url in action.
- `templates/base.html` — Add session-based navigation links.

## Files to create
- `tests/test_login_logout.py` — Automated tests covering login form rendering, valid authentication, invalid credentials, input validation, session persistence, logout session clearing, and conditional navbar links.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified with werkzeug (`check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Store `user_id` and `user_name` in Flask `session` upon successful login.
- Generic error message on bad credentials: `"Invalid email or password."` to avoid user enumeration.
- Logout must clear the session completely with `session.clear()`.
- Validate input presence (both email and password required).

## Definition of done
- [ ] Navigating to `GET /login` renders the login form with Email and Password fields.
- [ ] Submitting empty fields on `POST /login` displays a validation error message.
- [ ] Submitting invalid credentials (wrong email or incorrect password) displays `"Invalid email or password."`.
- [ ] Failed login attempts retain the entered `email` in the form.
- [ ] Submitting valid credentials authenticates the user, sets `session['user_id']` and `session['user_name']`, and redirects to `/profile`.
- [ ] Navigating to `GET /logout` clears `session` and redirects to `/login`.
- [ ] Navbar conditionally displays "Sign in" / "Get started" when logged out, and "Profile" / "Sign out" when logged in.
- [ ] All database queries use parameterized SQL.
- [ ] All automated tests in `tests/test_login_logout.py` pass.
