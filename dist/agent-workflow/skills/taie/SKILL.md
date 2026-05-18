---
name: taie
description: >
  Use when developing a new feature, adding functionality, or making
  substantial single-file modifications. Handles risk assessment, user
  approval, code writing with AST-level regression validation.
  Do NOT use for single-line fixes (use yindan) or multi-file refactoring (use sanjian).
---

# Standard Feature Development

## Workflow

1. Assess risk: identify target file, summarize proposed changes, list potential impacts.
2. Present risk assessment to user. Wait for approval.
3. If user denies → abort.
4. Write code to target file.
5. Run regression validation:
   a. py_compile syntax check.
   b. AST-level checks:
      - No imports from known-dangerous modules.
      - No empty function bodies (pass-only).
6. If validation fails → rollback to original (or delete if new file).

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/risk_assessor.py` | Evaluate change risk, request approval | `target_file`, `proposed_changes`, `auto_approve` | `{approved, report}` |
| `scripts/standard_write.py` | Write + AST regression + rollback | `filepath`, `content` | Success/failure message |

## Rules

- Never write without prior risk assessment and user approval.
- Regression checks are mandatory, not optional.
- If regression detects dangerous patterns → rollback immediately, report what was found.
- Scope is single-file. For multi-file work, defer to sanjian.
