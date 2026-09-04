---
name: review-code
description: >-
  Coordinates code-review and security-review subagents to audit code quality, PEP 8 standards,
  and security protections across Spendly.
argument-hint: "<optional: files, diff, or specific feature to review>"
---

# Review Code Skill (`/review-code`)

Use this skill when the user runs `/review-code` or asks for a combined code quality and security review.

---

## Workflow Execution

1. **Identify Review Scope**: Check unstaged/staged git diff or specified files in user input (`$ARGUMENTS`).
2. **Dispatch `code_reviewer` Subagent**:
   - Analyzes Python style, PEP 8, readability, error handling, and template architecture.
   - Generates code quality findings with refactoring suggestions.
3. **Dispatch `security_reviewer` Subagent**:
   - Analyzes SQL parameterization, route auth guards, session management, IDOR vulnerabilities, and password cryptography.
   - Generates vulnerability findings and mitigations.
4. **Synthesize Final Audit Report**:
   - Consolidate both reviews into a unified report with overall health verdict, critical security alerts, and prioritized code quality improvements.
