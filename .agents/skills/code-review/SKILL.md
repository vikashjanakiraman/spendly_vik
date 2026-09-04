---
name: code-review
description: >-
  Performs comprehensive code quality, PEP 8 compliance, architecture, and maintainability reviews for Spendly.
---

# Code Review Skill

This skill guides deep code quality inspections across the Spendly Flask/SQLite codebase.

---

## 1. Review Dimensions

### A. Python & PEP 8 Standards
- **Style & Formatting**: Verify consistent indentation (4 spaces), snake_case for functions/variables, PascalCase for classes, and UPPER_CASE for constants.
- **Type Safety & Docstrings**: Ensure public route handlers and database helpers have clear docstrings and well-defined parameters/return types.
- **Error Handling**: Verify robust `try/except` blocks with specific exception handling (avoiding bare `except:`).

### B. Flask & Database Best Practices
- **Database Access**: Ensure all database operations strictly use `database.db.get_db()`.
- **Resource Management**: Check that database connections are managed properly within the Flask request lifecycle.
- **Template Contexts**: Verify that templates receive clean, well-structured context variables rather than raw unformatted objects.
- **DRY Principle**: Identify redundant queries, duplicated route logic, or repeated HTML blocks that should be Jinja macros or partials.

---

## 2. Review Output Format

Structure the review feedback as follows:

1. **Summary of Changes**: Brief overview of files and functionality reviewed.
2. **Quality Highlights**: Positive patterns, good abstractions, and clean implementations.
3. **Actionable Suggestions**:
   - **Severity**: High / Medium / Low
   - **File & Line**: Exact reference (e.g. `app.py:L45-L52`)
   - **Issue**: Explanation of code smell, inefficiency, or style violation
   - **Suggested Improvement**: Concrete code snippet showing the refactored code
