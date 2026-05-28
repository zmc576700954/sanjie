---
name: sanjian
description: >
  Use when performing multi-file refactoring, code restructuring, architecture
  reorganization, or large-scale content integration. Handles task decomposition,
  dependency analysis, scope-controlled execution with backup/rollback, and
  result aggregation. Requires explicit user approval before execution.
  NOT for: single-file fixes or new feature development (use taie or yindan).
  NOT for: difficulty assessment without refactoring intent (use bajiu).
  NOT for: simple single-line text replacement (use yindan).
  Trigger when the user wants to RESTRUCTURE, REFACTOR, MIGRATE, or REORGANIZE
  code across MULTIPLE files, or change the ARCHITECTURE of a module.
trigger_keywords:
  high_confidence:
    - "多文件重构"
    - "架构重组"
    - "模块拆分"
    - "代码迁移"
    - "跨文件重构"
    - "multi-file refactoring"
    - "architecture restructure"
    - "module split"
    - "code migration"
    - "decouple"
    - "拆成微服务"
    - "拆成三层"
    - "解耦"
    - "untangle"
    - "god object"
    - "monolith"
    - "整体迁移到"
    - "全面重构"
    - "大规模改动"
    - "major refactor"
    - "overhaul"
    - "restructure"
    - "reorganize"
  medium_confidence:
    - "重构"
    - "重组"
    - "迁移"
    - "refactor"
    - "migrate"
    - "多个文件"
    - "跨文件"
    - "循环依赖"
    - "dependency"
    - "依赖关系"
    - "拓扑"
    - "接口变更"
    - "同时动"
    - "大改"
    - "升级到"
    - "适配"
  requires_context:
    - "重构" → only when context involves MULTIPLE files or architectural changes (single-line formatting is NOT refactoring)
    - "迁移" → only when context involves moving code between architectures/frameworks (not data migration)
negative_keywords:
  - "单个文件"
  - "一处"
  - "single file"
  - "就改一处"
  - "一行"
  - "改个typo"
risk_level: high
guard_rules:
  - name: scope_guardian
    required: true
    parameters:
      max_files: 10
      allowed_extensions: [".py", ".md"]
  - name: backup
    required: true
  - name: syntax_validation
    required: true
  - name: rollback
    required: true
tools:
  - name: dependency_analyzer
    script: "scripts/dependency_analyzer.py"
    parameters:
      target_files: "List of file paths to analyze."
      project_root: "Project root directory."
  - name: task_decomposer
    script: "scripts/task_decomposer.py"
    parameters:
      task_context: "Description of what needs to be refactored."
      target_files: "List of file paths to operate on."
  - name: scope_guardian
    script: "scripts/scope_guardian.py"
    parameters:
      subtask: "Subtask dictionary {id, target_file, operation, scope_level}."
      current_scope: "Currently authorized scope level."
      auto_approve: "Skip user input."
  - name: executor
    script: "scripts/executor.py"
    parameters:
      filepath: "Target file path."
      content: "New file content."
      operation: "REWRITE / RESTRUCTURE / INTEGRATE."
  - name: result_integrator
    script: "scripts/result_integrator.py"
    parameters:
      execution_results: "List of result dicts."
      task_context: "Original task description."
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
