---
name: test-writer
description: >-
  Writes comprehensive, robust pytest unit and integration test cases for Spendly routes,
  database operations, and user workflows.
---

# Test Writer Skill

This skill guides the creation of high-quality `pytest` test suites for the Spendly expense tracker application.

---

## 1. Responsibilities

- Analyze routes in `app.py`, database schema and queries in `database/db.py`, and templates in `templates/`.
- Identify test coverage requirements:
  - **Happy Paths**: Successful GET and POST requests, valid redirects, proper database mutations.
  - **Error & Validation Paths**: Missing required fields, invalid formats, duplicate emails, invalid credentials, out-of-range amounts.
  - **Authorization & Security**: Protected routes redirecting unauthenticated users to `/login`, password hashing verification via `check_password_hash`.
  - **Database Integrity**: Proper foreign key cascades/nullifications, transaction rollbacks.
- Write idiomatic test functions in `tests/test_<feature>.py`.

---

## 2. Test Structure & Fixture Patterns

Always adhere to the established fixtures in `tests/conftest.py`:

```python
import pytest
from database.db import get_db
from werkzeug.security import check_password_hash


def test_example_feature(client, app):
    """Test description stating the expected behavior."""
    # 1. Arrange / Pre-condition
    # 2. Act
    response = client.post("/endpoint", data={"key": "value"}, follow_redirects=False)

    # 3. Assert HTTP status and redirects
    assert response.status_code == 302
    assert response.headers["Location"] == "/expected-destination"

    # 4. Assert Database state
    with app.app_context():
        db = get_db()
        record = db.execute("SELECT * FROM table_name WHERE key = ?", ("value",)).fetchone()
        assert record is not None
```

---

## 3. Best Practices for Writing Tests

- **Descriptive Names**: Name test functions clearly, e.g. `test_login_invalid_password_shows_error(client)`.
- **Docstrings**: Include a brief docstring explaining what is being tested.
- **Independence**: Ensure tests do not depend on execution order or persistent state across runs.
- **Meaningful Assertions**: Always assert both the response code and content/redirect, as well as database state when mutations occur.
