---
name: yindan
description: >
  Use when performing a precise, minimal-scope code fix on a single known
  location. Handles exact text replacement with regression validation.
  NOT for: multi-file changes, new features, adding logic, or unclear targets.
  NOT for: adding new parameters, conditions, or features (use taie).
  NOT for: global/bulk replacements across files (use kaishan).
  NOT for: architectural changes or refactoring (use sanjian).
  Distinguishing from taie: yindan only REPLACES existing text (rename, change value,
  fix typo). taie adds NEW logic (new parameters, new conditions, new features).
trigger_keywords:
  high_confidence:
    - "精准修复"
    - "精确替换"
    - "单点替换"
    - "单处修改"
    - "只改一处"
    - "就改这一处"
    - "就这一处"
    - "仅此一处"
    - "precise fix"
    - "exact replacement"
    - "single spot"
    - "targeted fix"
    - "one spot"
    - "把X换成Y"
    - "改个typo"
    - "修个typo"
    - "变量重命名"
    - "rename variable"
    - "修改一处"
    - "最小范围"
  medium_confidence:
    - "改成"
    - "替换成"
    - "swap"
    - "change"
    - "变量名"
    - "配置项"
    - "off-by-one"
    - "一个数字"
    - "就一个"
  requires_context:
    - "重构一行" → only when context is purely text replacement (no logic change)
    - "改成" → only when there is a clear old→new mapping in a single location
negative_keywords:
  - "多个文件"
  - "批量"
  - "全局"
  - "bulk"
  - "mass"
  - "所有文件"
  - "添加功能"
  - "add feature"
  - "添加参数"
  - "新功能"
tools:
  - name: precise_fix
    script: "scripts/precise_fix.py"
    parameters:
      filepath: "Target file path."
      old_str: "Exact text to find and replace. Must be non-empty."
      new_str: "Replacement text. Can be empty for deletion."
---

# Precision Fix

## Workflow

1. Validate inputs: types, non-empty old_str, path safety, file existence.
2. Verify old text exists in file. If not found -> abort, do not guess.
3. Replace old text with new text (single occurrence).
4. Validate:
   a. Read file back, confirm new_str is present AND old_str is gone.
   b. If .py file, run py_compile syntax check.
5. If validation fails -> rollback to original content.
6. Log change to stderr for audit traceability.

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/precise_fix.py` | Text replace + validate + rollback | `filepath`, `old_str`, `new_str` | Success/failure message |

## MCP Server

| Server | Location |
|--------|----------|
| `mcp-servers/yindan_server.py` | MCP tool adapter exposing `precise_fix` |

Run with: `python mcp-servers/yindan_server.py`

## Rules

- One file, one replacement per invocation. No batch operations.
- If `old_str` not found in file, refuse to proceed. Never do fuzzy matching.
- `old_str` must be a non-empty string. Empty strings are rejected.
- Always validate after write. Always rollback on failure.
- Do not touch any code outside the specified replacement target.
- Files larger than 100 MB are rejected to prevent memory exhaustion.
- Only .py files receive syntax validation; other file types skip this step.
