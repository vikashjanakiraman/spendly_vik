---
name: security-review
description: >-
  Audits security, authentication, session integrity, SQL injection vectors, and password handling for Spendly.
---

# Security Review Skill

This skill guides thorough application security audits across the Spendly Flask/SQLite codebase.

---

## 1. Security Audit Checklist

### A. SQL Injection Prevention
- **Parameterized Queries**: Verify every SQL query uses placeholder parameters (`?`) rather than Python f-strings, string formatting (`%s`), or string concatenation (`+`).
- **Dynamic Identifiers**: If column names or sort orders are dynamic, ensure they are strictly validated against an explicit whitelist.

### B. Authentication & Authorization
- **Route Protection**: Ensure all private routes check `session.get('user_id')` or use a `@login_required` decorator and redirect unauthenticated requests to `/login`.
- **Horizontal Privilege Escalation (IDOR)**: Ensure database queries filtering user data include `WHERE user_id = ?` to prevent users from accessing or modifying records belonging to other users.
- **Session Integrity**: Verify sessions are cleared on logout via `session.clear()`.

### C. Cryptography & Password Safety
- **Password Hashing**: Ensure plain-text passwords are never logged, stored, or compared directly.
- **Hashing Algorithms**: Strictly verify the use of `werkzeug.security.generate_password_hash` and `werkzeug.security.check_password_hash`.

### D. Web Vulnerabilities (OWASP)
- **Cross-Site Scripting (XSS)**: Ensure user-supplied data rendered in templates is auto-escaped by Jinja2 (avoid unsafe `| safe` filter on un-sanitized user content).
- **Sensitive Data Exposure**: Check that stack traces, database credentials, or secret keys are not exposed to users in production responses.

---

## 2. Audit Output Format

Structure security findings as:

- **Security Assessment Summary**: (Secure / Warning / Critical Vulnerabilities Found)
- **Vulnerability Findings**:
  - **Risk Level**: [CRITICAL] / [HIGH] / [MEDIUM] / [LOW]
  - **Location**: `file_path:line_number`
  - **Vulnerability Type**: (e.g. Broken Access Control, SQL Injection, Plaintext Password Handling)
  - **Attack Scenario**: How this could be exploited
  - **Remediation**: Exact code fix required
