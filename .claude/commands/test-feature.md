---
description: Author, review, and verify test cases for a feature using test_writer and test_reviewer subagents
argument-hint: "<feature_name or route, e.g. profile, payment, register>"
---

# Test Feature Command (`/test-feature`)

Coordinate `test_writer` and `test_reviewer` subagents to author and review test cases for `$ARGUMENTS`.

1. **Test Writer**:
   - Inspect `app.py`, `database/db.py`, and `templates/`.
   - Write comprehensive tests in `tests/test_<feature>.py` covering status codes, database mutations, redirects, and session security.

2. **Test Reviewer**:
   - Run `pytest tests/test_<feature>.py -v`.
   - Audit assertions, test isolation, and edge cases.
   - Propose or apply corrections for any gaps.

3. **Full Regression**:
   - Run `pytest` and provide a summary report.
