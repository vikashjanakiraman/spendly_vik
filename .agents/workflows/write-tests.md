---
description: Write and implement new pytest test cases for Spendly features and routes
allowed-tools: Read, Write, Bash(pytest:*,python3:*)
---

# Write Tests Workflow

1. Read the feature implementation in `app.py`, `database/db.py`, and `templates/`.
2. Determine required test cases:
   - GET routes (rendering, context data)
   - POST routes (valid data, redirects, database mutations)
   - Validation & error conditions (missing fields, duplicate inputs)
   - Session & security checks (unauthenticated redirects, password hashing)
3. Check existing tests in `tests/` to prevent duplication and follow existing conventions.
4. Implement new test functions in `tests/test_<feature>.py`.
5. Run `pytest tests/test_<feature>.py` to verify tests execute properly.
