---
name: yindan
description: >
  Use when performing a precise, minimal-scope code fix on a single known
  location. Handles exact text replacement with regression validation.
  Do NOT use for multi-file changes, new features, or unclear targets.
tools:
  - name: precise_fix
    script: "scripts/precise_fix.py"
    parameters:
      filepath: "Target file path."
      old_str: "Exact text to find and replace."
      new_str: "Replacement text."
---

# Precision Fix

## Workflow

1. Receive exact target: file path, old text, new text.
2. Verify old text exists in file. If not found → abort, do not guess.
3. Replace old text with new text (single occurrence).
4. Validate:
   a. Read file back, confirm new text is present.
   b. If .py file, run py_compile syntax check.
5. If validation fails → rollback to original content.

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/precise_fix.py` | Text replace + validate + rollback | `filepath`, `old_str`, `new_str` | Success/failure message |

## Rules

- One file, one replacement per invocation. No batch operations.
- If `old_str` not found in file, refuse to proceed. Never do fuzzy matching.
- Always validate after write. Always rollback on failure.
- Do not touch any code outside the specified replacement target.
