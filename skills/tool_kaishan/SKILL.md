---
name: kaishan
description: >
  Use when performing bulk file deletion, mass regex replacement, or
  large-scale deprecated code cleanup. Handles impact assessment, mandatory
  user authorization, execution, and destruction logging.
  Do NOT use for targeted fixes or feature development.
tools:
  - name: blast_assessor
    script: "scripts/blast_assessor.py"
    parameters:
      directory: "Target directory to scan."
      pattern: "Regex pattern to match files."
      action_type: "DELETE or REPLACE."
      auto_approve: "Skip user input."
  - name: bulk_operations
    script: "scripts/bulk_operations.py"
    parameters:
      affected_files: "List of file paths."
      old_pattern: "Regex pattern to find (for replace)."
      new_str: "Replacement text (for replace)."
---

# Bulk Destructive Operations

## Workflow

1. Define scope (three questions): target directory, match pattern, action type (DELETE or REPLACE).
2. Dry-run: scan for all affected files, count impact.
3. Present impact assessment to user with file list. Wait for explicit approval.
4. If user denies → abort entirely.
5. Execute bulk operation (delete or regex replace).
6. Write destruction log to `.trae/kaishan_logs/destruction_log_<timestamp>.md`.

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/blast_assessor.py` | Scan affected files, request approval | `directory`, `pattern`, `action_type`, `auto_approve` | `{approved, affected_files}` |
| `scripts/bulk_delete.py` | Delete files + write log | `affected_files` | Success message with log path |
| `scripts/global_replace.py` | Regex replace across files + write log | `affected_files`, `old_pattern`, `new_str` | Success message with log path |

## Rules

- Never execute without explicit user approval. No exceptions.
- Always write a destruction log after execution.
- If scope is unclear (missing directory, pattern, or action type), ask for clarification before proceeding.
- Destruction is irreversible. The log is the only recovery reference.
