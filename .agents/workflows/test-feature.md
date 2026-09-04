---
description: Automatically author, review, and verify test cases for a feature by coordinating test_writer and test_reviewer subagents
argument-hint: "<feature_name or route, e.g. profile, payment, register>"
allowed-tools: Read, Write, Bash(pytest:*,python3:*), Subagent(test_writer,test_reviewer)
---

# Test Feature Workflow (`/test-feature`)

Coordinate the `test_writer` and `test_reviewer` subagents to author comprehensive test cases and perform a thorough QA audit for the specified feature.

User input / Target Feature: `$ARGUMENTS`

---

## Step 1 — Parse Target Feature

1. Identify the target feature or module from `$ARGUMENTS` (e.g. `profile`, `payment`, `register`, `login`, `expenses`, `all`).
2. If no argument is provided, inspect git diff or recent changes to determine the target feature, or prompt for clarification if ambiguous.

---

## Step 2 — Invoke Test Writer Subagent (`test_writer`)

Invoke the `test_writer` subagent to generate test cases:

- **Goal**: Write complete unit and integration tests for the target feature.
- **Context to examine**:
  - Routes in `app.py`
  - Database schema & helper functions in `database/db.py`
  - Relevant templates in `templates/`
- **Coverage requirements**:
  1. Happy paths (valid submissions, proper redirects, 200/302 status codes).
  2. Input validation & error states (missing fields, duplicate data, flash errors).
  3. Authentication & session security (unauthenticated redirects to `/login`).
  4. Database state assertions (verifying rows inserted/updated/deleted with `get_db()`).
- **Target test file**: `tests/test_<feature>.py`

Wait for `test_writer` to complete and return the generated test suite.

---

## Step 3 — Invoke Test Reviewer Subagent (`test_reviewer`)

Invoke the `test_reviewer` subagent to audit and validate the new test suite:

- **Goal**: Audit test quality, assertion rigor, and test isolation.
- **Review Checklist**:
  1. Run `pytest tests/test_<feature>.py -v`.
  2. Check assertion strength (ensure tests assert DB state and response content, not just status codes).
  3. Verify security checks (e.g., password hashing tested via `check_password_hash`).
  4. Ensure no test isolation leaks or shared mutable state.
- **Feedback & Corrections**:
  - If test reviewer finds gaps or failures, have `test_writer` fix the test cases or adjust the implementation.

---

## Step 4 — Full Suite Regression & Report

1. Run the entire test suite to ensure zero regressions:
   ```bash
   pytest -v
   ```
2. Present a structured final summary to the user:
   - **Feature Tested**: Name of the target module.
   - **Test File**: Path to `tests/test_<feature>.py`.
   - **Total Tests Added/Updated**: Count and descriptions.
   - **Pytest Results**: Pass/Fail summary and execution time.
