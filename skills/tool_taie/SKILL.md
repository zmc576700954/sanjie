---
name: taie
description: >
  Use when developing a NEW FEATURE, adding functionality, or making
  substantial single-file modifications. Handles risk assessment, user
  approval, code writing with AST-level regression validation.
  NOT for: single-line text replacement (use yindan).
  NOT for: multi-file refactoring (use sanjian).
  NOT for: bug investigation without implementation (use tianyan or nezha_skill).
  Distinguishing from yindan: taie adds NEW LOGIC (new parameters, new conditions,
  new features). yindan only REPLACES TEXT (rename a variable, change a value).
trigger_keywords:
  high_confidence:
    - "新功能"
    - "添加功能"
    - "实现功能"
    - "开发功能"
    - "add feature"
    - "implement feature"
    - "new feature"
    - "build feature"
    - "enhance"
    - "写一个新的"
    - "需要一个功能"
    - "scaffold"
    - "新增模块"
    - "添加一个默认参数"
    - "添加参数"
    - "添加条件"
    - "添加验证"
    - "add parameter"
    - "add validation"
    - "add condition"
    - "webhook"
    - "endpoint"
    - "middleware"
    - "handler"
    - "认证功能"
    - "通知功能"
    - "权限管理"
    - "文件上传"
    - "导出功能"
    - "筛选功能"
  medium_confidence:
    - "开发"
    - "实现"
    - "功能"
    - "feature"
    - "develop"
    - "implement"
    - "add"
    - "增强"
  requires_context:
    - "实现" → only when context involves NEW functionality (not fixing existing code)
    - "开发" → only when context involves feature creation (not maintenance)
    - "添加" → only when context involves adding LOGIC/BEHAVIOR (not just changing text)
negative_keywords:
  - "改一行"
  - "就一处"
  - "typo"
  - "单点"
  - "重命名"
  - "rename"
  - "把X换成Y"
tools:
  - name: risk_assessor
    script: "scripts/risk_assessor.py"
    parameters:
      target_file: "File to be modified."
      proposed_changes: "Description of planned changes."
      auto_approve: "Skip user input."
  - name: standard_write
    script: "scripts/standard_write.py"
    parameters:
      filepath: "Target file path."
      content: "New file content."
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
      - No imports from known-dangerous modules (os, subprocess, importlib).
      - No indirect dangerous calls (__import__, getattr, __builtins__ access).
      - No empty function bodies (pass-only, ellipsis-only, or any combination).
6. If validation fails → rollback to original (or delete if new file).

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/risk_assessor.py` | Evaluate change risk, request approval | `target_file`, `proposed_changes`, `auto_approve` | `{approved, report}` |
| `scripts/standard_write.py` | Write + AST regression + rollback | `filepath`, `content` | `{success, message, details?}` |
| `scripts/security_config.py` | Centralized security rules (dangerous modules, builtins, policies) | — | Config constants |

## Return Value Format

### standard_write

```json
{
  "success": true,
  "message": "Write complete, passed validation."
}
```

On failure:

```json
{
  "success": false,
  "message": "Regression validation failed. Action: rolled_back. Detail: ...",
  "details": {
    "error": "Dangerous call detected: os.system (via alias 'myos')",
    "action": "rolled_back"
  }
}
```

### risk_assessor

```json
{
  "approved": true,
  "report": "Risk Assessment:\n  Target: ..."
}
```

Or when approval is required:

```json
{
  "approved": false,
  "report": "...",
  "approval_required": true,
  "message": "Risk assessment for ... requires approval."
}
```

## Security Configuration

All dangerous-module lists, builtin names, and detection policies live in
`scripts/security_config.py`. Extend there — do not hard-code in logic.

Current dangerous modules: `os`, `subprocess`, `importlib`.

## Covered Detection Patterns

| Pattern | Example | Status |
|---------|---------|--------|
| Direct call | `os.system('cmd')` | Blocked |
| Aliased import | `import os as m; m.system()` | Blocked |
| From-import | `from os import system; system()` | Blocked |
| `__import__` indirect | `__import__('os').system()` | Blocked |
| `getattr` reflection | `getattr(os, 'system')()` | Blocked |
| `importlib.import_module` | `importlib.import_module('os')` | Blocked |
| `__builtins__` subscript | `globals()['__builtins__']['eval']` | Blocked |
| `__builtins__` attribute | `vars()['__builtins__'].exec` | Blocked |
| Nested import (func/class/try/if) | `def f(): import os; os.system()` | Blocked |
| Empty function (pass) | `def f(): pass` | Blocked |
| Empty function (ellipsis) | `def f(): ...` | Blocked |
| Empty function (mixed) | `def f(): ...\n    pass` | Blocked |

## Rules

- Never write without prior risk assessment and user approval.
- Regression checks are mandatory, not optional.
- If regression detects dangerous patterns → rollback immediately, report what was found.
- Scope is single-file. For multi-file work, defer to sanjian.
