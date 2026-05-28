---
name: kaishan
description: >
  Use when performing bulk file deletion, mass regex replacement, or
  large-scale deprecated code cleanup. Handles impact assessment, mandatory
  user authorization, execution, and destruction logging.
  NOT for: targeted single-file fixes (use yindan).
  NOT for: feature development (use taie) or multi-file refactoring (use sanjian).
  NOT for: difficulty assessment without execution intent (use bajiu).
  Trigger when the user wants to DELETE, REMOVE, CLEAN UP, or REPLACE
  across multiple files or directories at once.
  Recognizes colloquial/implicit expressions: "清掉", "删掉", "不要了",
  "太烦了" + file operation, "干掉", "弄走", "一并清理".
trigger_keywords:
  high_confidence:
    - "批量删除"
    - "全部删除"
    - "大量清理"
    - "全局替换"
    - "正则替换"
    - "废弃代码"
    - "bulk delete"
    - "mass cleanup"
    - "global replace"
    - "deprecated removal"
    - "delete all"
    - "remove all"
    - "project-wide replace"
    - "清掉"
    - "删掉"
    - "都删了"
    - "整个删掉"
    - "不要了"
    - "干掉"
    - "弄走"
    - "一并清理"
    - "nuke"
    - "purge"
    - "wipe"
  medium_confidence:
    - "清理"
    - "清除"
    - "替换所有"
    - "过期的"
    - "旧的"
    - "废弃"
    - "legacy"
    - "deprecated"
    - "clean up"
    - "blast radius"
    - "影响范围"
    - "日志文件"
    - ".log"
    - "cache"
    - "fixture"
    - "太烦了"
    - "没必要了"
    - "过时了"
  requires_context:
    - "太烦了" → only when context involves repetitive file operations
    - "影响范围" → only when context involves deletion or replacement scope
negative_keywords:
  - "精准"
  - "就一处"
  - "只改一行"
  - "单点"
  - "precise"
  - "single spot"
  - "一处"
tools:
  - name: blast_assessor
    script: "scripts/blast_assessor.py"
    parameters:
      directory: "Target directory to scan."
      pattern: "Regex pattern to match files."
      action_type: "DELETE or REPLACE."
      auto_approve: "Skip user input."
      max_depth: "Maximum recursion depth. 0 = unlimited. Prevents runaway scans on symlink loops."
  - name: bulk_operations
    script: "scripts/bulk_operations.py"
    parameters:
      affected_files: "List of file paths."
      old_pattern: "Regex pattern to find (for replace)."
      new_str: "Replacement text (for replace)."
      base_dir: "Base directory for log output. Defaults to os.getcwd()."
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
| `scripts/blast_assessor.py` | Scan affected files, request approval | `directory`, `pattern`, `action_type`, `auto_approve`, `max_depth` | `{approved, affected_files}` |
| `scripts/bulk_operations.py` — `bulk_delete()` | Delete files + write log | `affected_files`, `base_dir` | Success message with log path |
| `scripts/bulk_operations.py` — `global_replace()` | Regex replace across files + write log | `affected_files`, `old_pattern`, `new_str`, `base_dir` | Success message with log path |

## Rules

- Never execute without explicit user approval. No exceptions.
- Always write a destruction log after execution.
- If scope is unclear (missing directory, pattern, or action type), ask for clarification before proceeding.
- Destruction is irreversible. The log is the only recovery reference.

## Notes

- **Symlinks**: `assess_blast_radius` does not follow symbolic links by default (`followlinks=False`). Use `max_depth` to cap recursion depth on deep or circular trees.
- **Log rotation**: At most 200 log files are kept (configurable via `MAX_LOG_FILES` in `bulk_operations.py`). Older logs are deleted automatically.
- **Error isolation**: `bulk_delete` continues processing remaining files if one fails. Failed and skipped files are recorded in the log.
- **Regex pre-compilation**: Both `assess_blast_radius` and `global_replace` pre-compile the regex pattern. Invalid patterns are caught immediately without processing any files.
- **Disk-full protection**: `_write_log` catches `OSError` on write and returns an error string instead of crashing.
