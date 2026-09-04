---
name: test-reviewer
description: >-
  Reviews, audits, and executes pytest test suites in Spendly. Verifies assertion strength,
  test isolation, edge case coverage, and reports test outcomes.
---

# Test Reviewer Skill

This skill guides the review, validation, and audit of tests written for the Spendly expense tracker.

---

## 1. Responsibilities

- **Execute Test Suites**: Run `pytest -v` across individual modules or the entire test directory.
- **Audit Assertion Quality**:
  - Verify that tests don't just assert status codes (e.g., `status_code == 200`), but also verify response HTML/data and underlying database side-effects.
  - Verify that password hashing is validated with `check_password_hash` rather than direct equality checks.
  - Check that negative tests properly assert the rendered error messages or flash banners.
- **Check Isolation & Teardown**:
  - Confirm tests rely on `client` / `app` fixtures in `tests/conftest.py` with temporary SQLite databases.
  - Ensure tests do not leak global state or fail when run in random order.
- **Identify Coverage Gaps**:
  - Flag missing edge cases (e.g. boundary values, SQL injection attempts, unauthenticated access).

---

## 2. Review Checklist

When checking test cases, verify:

1. [ ] **Execution**: Do all tests pass with `pytest`?
2. [ ] **Auth Coverage**: Are protected routes tested with and without valid session credentials?
3. [ ] **Validation Coverage**: Are empty strings, whitespace, missing fields, and duplicates tested?
4. [ ] **DB State Verification**: Do POST routes verify the database record was actually inserted/updated/deleted?
5. [ ] **Foreign Key Constraints**: Are cascades or nullifications tested where appropriate?
6. [ ] **Assertion Rigor**: Are assertions specific rather than overly broad or trivial?

---

## 3. Reporting Format

Provide feedback structured as:
- **Test Execution Summary**: (e.g., X passed, Y failed)
- **Strengths**: What the test suite covers effectively
- **Gaps / Weaknesses**: Missing assertions, unhandled edge cases, or false positives
- **Actionable Recommendations**: Specific changes or additions required
