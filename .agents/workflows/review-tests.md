---
description: Review, audit assertion quality, and run pytest test cases for Spendly
allowed-tools: Read, Bash(pytest:*,python3:*)
---

# Review Tests Workflow

1. Execute the entire test suite with verbose output:
   ```bash
   pytest -v
   ```
2. Inspect test files in `tests/` for:
   - Database mutation assertions (ensuring DB state is asserted after POST requests)
   - Proper session mock/fixture usage and unauthenticated redirect checks
   - Strong assertions vs shallow status code checks
3. Check for test isolation and clean teardown of temporary databases.
4. Output an audit report with pass/fail statistics, coverage evaluation, and suggestions.
