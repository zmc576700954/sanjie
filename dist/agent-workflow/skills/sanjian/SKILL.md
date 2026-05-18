---
name: sanjian
description: >
  Use when performing multi-file refactoring, code restructuring, architecture
  reorganization, or large-scale content integration. Handles task decomposition,
  dependency analysis, scope-controlled execution with backup/rollback, and
  result aggregation. Requires explicit user approval before execution.
  Do NOT use for single-file fixes or new feature development.
---

# Multi-File Refactoring Executor

## Workflow

1. Analyze dependencies between target files using AST import parsing.
2. Decompose task into subtasks, each with:
   - Target file path
   - Operation type: REWRITE / RESTRUCTURE / INTEGRATE
   - Scope level: SAFE / BOUNDARY / DEEP
   - Dependencies on other subtasks
3. Sort subtasks by dependency topology (modify leaf nodes first, interfaces last).
4. For each subtask in order:
   a. Check scope level against current authorization.
   b. If scope exceeds authorization → pause and request user approval to expand.
   c. If user denies → skip this subtask, continue to next.
   d. Backup original file.
   e. Write new content.
   f. Validate syntax (py_compile for .py files).
   g. If validation fails → rollback from backup.
5. Aggregate results: count succeeded/failed/skipped, list backup paths.

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/dependency_analyzer.py` | Parse imports, build dependency graph | `target_files`, `project_root` | `{graph, reverse_deps, topological_order, circular_deps}` |
| `scripts/task_decomposer.py` | Split task into ordered subtasks | `task_context`, `target_files` | `{subtasks, execution_order}` |
| `scripts/scope_guardian.py` | Check/expand scope authorization | `subtask`, `current_scope`, `auto_approve` | `{approved, authorized_scope, action}` |
| `scripts/executor.py` | Backup + write + validate + rollback | `filepath`, `content`, `operation` | `{success, backup_path, message}` |
| `scripts/result_integrator.py` | Aggregate execution results | `execution_results` | `{succeeded, failed, skipped, backup_files, status}` |

## Scope Levels

| Level | Meaning | Requires approval |
|-------|---------|-------------------|
| SAFE | Only modifies target file internals | No (if already authorized at SAFE) |
| BOUNDARY | May affect direct dependents (interface changes) | Yes, if current auth < BOUNDARY |
| DEEP | Cross-module cascading impact | Yes, if current auth < DEEP |

## Rules

- Always backup before writing. No exceptions.
- Validate syntax after every write. Rollback on failure.
- Never execute without user awareness — pause at scope expansion points.
- Process subtasks in dependency order: leaves first, shared interfaces last.
- If circular dependencies detected, flag to user before proceeding.

## References

- `references/refactoring_patterns.md` — Common refactoring strategies and when to apply each.
