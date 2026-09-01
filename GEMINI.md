# Project: Spendly (Expense Tracker)

## Overview
**Spendly** is a web-based personal finance and expense tracking application built with Python (Flask) and SQLite. It provides user authentication, expense categorization, financial tracking, and summary analytics.

---

## Tech Stack
- **Backend**: Python 3.13, Flask 3.x, Werkzeug (for password hashing and auth utilities)
- **Database**: SQLite3 with foreign keys enabled and `sqlite3.Row` row factory
- **Frontend**: HTML5, CSS3 (vanilla custom styling), JavaScript, Jinja2 templating
- **Testing**: `pytest`, `pytest-flask`

---

## Project Structure
```
expense-tracker/
├── app.py                  # Main Flask application and route definitions
├── database/
│   ├── __init__.py
│   ├── db.py               # Database connections, init_db, seed_db
│   └── spendly.db          # SQLite database file
├── static/
│   ├── css/
│   │   ├── style.css       # Global layout, variables, forms, buttons
│   │   └── landing.css     # Landing page styles
│   └── js/
│       └── main.js         # Client-side scripts & interactions
├── templates/
│   ├── base.html           # Base layout template
│   ├── landing.html        # Landing page
│   ├── register.html       # User registration
│   ├── login.html          # User authentication
│   ├── terms.html          # Terms and conditions
│   └── privacy.html        # Privacy policy
├── requirements.txt        # Python package dependencies
└── GEMINI.md               # Agent guidelines and project instructions
```

---

## Database Schema

### `users`
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT NOT NULL)
- `email` (TEXT NOT NULL UNIQUE)
- `password_hash` (TEXT NOT NULL)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

### `categories`
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT NOT NULL UNIQUE)
- `icon` (TEXT DEFAULT '🏷️')
- `color` (TEXT DEFAULT '#4F46E5')

### `expenses`
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `user_id` (INTEGER NOT NULL, FK -> `users(id)` ON DELETE CASCADE)
- `category_id` (INTEGER, FK -> `categories(id)` ON DELETE SET NULL)
- `title` (TEXT NOT NULL)
- `amount` (REAL NOT NULL)
- `date` (DATE NOT NULL)
- `notes` (TEXT)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

---

## Development Roadmap & Milestones

1. **Step 1: Database Setup** (`database/db.py`)
   - `get_db()`: SQLite connection with foreign keys and `row_factory = sqlite3.Row`.
   - `init_db()`: Schema migration with `CREATE TABLE IF NOT EXISTS`.
   - `seed_db()`: Seed default categories and demo user (`nitish@example.com` / `password123`).

2. **Step 2: Registration**
   - Implement `POST /register` with validation, duplicate email check, and password hashing.

3. **Step 3: Login & Logout**
   - Implement `POST /login` with session management and `GET /logout`.

4. **Step 4: User Profile**
   - Implement `/profile` with user details and edit capabilities.

5. **Step 5 & 6: Expense Dashboard & Overview**
   - Dashboard displaying expense summaries, monthly totals, and category breakdown.

6. **Step 7: Add Expense**
   - Route and form for adding new expense records linked to the active session user.

7. **Step 8: Edit Expense**
   - Route and form to update existing expense entries.

8. **Step 9: Delete Expense**
   - Route to delete an expense record.

---

## Coding Guidelines & Best Practices

- **Database Access**: Always use `database.db.get_db()` to obtain database connections. Ensure `PRAGMA foreign_keys = ON;` is active.
- **Security**: Never store plain-text passwords. Use `werkzeug.security.generate_password_hash` and `check_password_hash`.
- **Session Protection**: Protect authenticated routes by checking `session.get('user_id')` or with a `@login_required` decorator.
- **Error Handling**: Gracefully return user-facing error messages in forms (`error` variable in Jinja templates).
- **Code Style**: Follow PEP 8 standards, keep docstrings and comments clear.

---

## Common Commands

- **Run Database Setup & Seed**:
  ```bash
  python database/db.py
  ```
- **Start Development Server**:
  ```bash
  python app.py
  ```
- **Run Tests**:
  ```bash
  pytest
  ```
