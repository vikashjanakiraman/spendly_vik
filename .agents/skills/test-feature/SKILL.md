---
name: test-feature
description: >-
  Coordinates test_writer and test_reviewer subagents to author, audit, and verify
  test cases for a specific feature or route in Spendly.
argument-hint: "<feature_name or route, e.g. profile, payment, register>"
---

# Test Feature

Use this skill when the user runs `/test-feature` or asks to test a specific feature using the dedicated test writer and test reviewer subagents.

---

## Workflow Execution

1. **Identify Feature Target**: Extract the target feature or module from user arguments or recent git diff.
2. **Dispatch `test_writer` Subagent**:
   - Inspect `app.py`, `database/db.py`, and `templates/`.
   - Write comprehensive tests in `tests/test_<feature>.py`.
   - Ensure coverage of happy paths, validation errors, session checks, and database mutations.
3. **Dispatch `test_reviewer` Subagent**:
   - Run `pytest tests/test_<feature>.py -v`.
   - Audit assertions, security checks, and test isolation.
   - Refine tests if any weaknesses or failures are flagged.
4. **Run Regression & Summary**:
   - Run `pytest` across all suites.
   - Report final outcome with test counts and verification details.
