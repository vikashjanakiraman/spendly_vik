---
description: Run combined code quality and security review using code_reviewer and security_reviewer subagents
argument-hint: "<optional: files, git diff, or feature to review>"
allowed-tools: Read, Bash(git:*), Subagent(code_reviewer,security_reviewer)
---

# Review Code Workflow (`/review-code`)

Coordinate the `code_reviewer` and `security_reviewer` subagents to perform a thorough code quality and security audit.

Target / Scope: `$ARGUMENTS`

---

## Step 1 — Determine Review Scope

1. If specific files or modules are provided in `$ARGUMENTS`, target those files.
2. Otherwise, check git changes (`git diff main...HEAD` or `git status` / `git diff`) to review all recent modifications.
3. If no uncommitted or branch changes exist, audit key core modules (`app.py`, `database/db.py`, `templates/`).

---

## Step 2 — Invoke Code Review Subagent (`code_reviewer`)

Invoke `code_reviewer` subagent:
- **Scope**: Inspect target files for PEP 8 compliance, error handling, function modularity, template cleanliness, and SQLite query patterns.
- **Output**: Code quality rating, strengths, and actionable refactoring suggestions.

---

## Step 3 — Invoke Security Review Subagent (`security_reviewer`)

Invoke `security_reviewer` subagent:
- **Scope**: Inspect target files for SQL injection (parameter placeholders), authentication route guards (`session.get('user_id')`), password hashing (`werkzeug.security`), IDOR protections (`WHERE user_id = ?`), and XSS risks.
- **Output**: Security assessment, vulnerability findings (Critical/High/Medium/Low), and remediation patches.

---

## Step 4 — Consolidated Review Report

Combine outputs into a unified report:
- **Audit Target & Files Checked**
- **Security Assessment** (Status: Passed / Action Required)
- **Code Quality Assessment** (Status: Passed / Improvements Suggested)
- **Action Items & Prioritized Fixes**
