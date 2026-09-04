---
description: Run automated test suite with pytest, verify database integrity, and report code quality status
allowed-tools: Read, Bash(pytest:*,python3:*)
---

# Automated Test & Quality Runner Workflow

1. Execute the full test suite using `pytest`:
   ```bash
   pytest -v
   ```

2. Check test outcomes:
   - If all tests pass, report the summary counts (total tests, passed, execution time).
   - If any tests fail, inspect the failure tracebacks, identify the offending file and line, and suggest or apply the fix.

3. Verify database integrity:
   - Ensure foreign key constraints and row factory configuration remain intact in `database/db.py`.
   - Verify that test databases created in `tests/conftest.py` are properly torn down after test execution.

4. Check route authentication protections:
   - Ensure all sensitive endpoints (e.g. `/profile`, `/checkout`, `/dashboard`) require an active session user ID.
