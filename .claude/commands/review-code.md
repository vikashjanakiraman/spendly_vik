---
description: Perform code quality and security review using code_reviewer and security_reviewer subagents
argument-hint: "<optional: files, git diff, or feature to review>"
---

# Review Code Command (`/review-code`)

Coordinate `code_reviewer` and `security_reviewer` subagents to review changes in `$ARGUMENTS`.

1. **Code Reviewer**:
   - Inspects target files for PEP 8, clarity, error handling, and architecture.
2. **Security Reviewer**:
   - Audits SQL queries, session handling, authentication guards, and password hashing.
3. **Consolidated Report**:
   - Delivers a prioritized summary of findings and remediation steps.
