---
name: tianyan
description: >
  Use when INVESTIGATING bugs, tracing business logic, diagnosing errors,
  or searching technical documentation. Handles deep root-cause analysis,
  logic chain tracing, and multi-source doc queries with cross-verification.
  Investigation only — never modifies code.
  NOT for: code modification, bug fixing, patching, or executing repairs (use nezha_skill).
  NOT for: git blame, file listing, reading code for understanding (no error involved).
  NOT for: security compliance checks or format audits (use wanglingguan_skill).
  Trigger ONLY when the user wants to FIND OUT WHY something is wrong,
  not when they want to FIX it. If user says "查并修" or "find and fix",
  prefer nezha_skill.
trigger_keywords:
  high_confidence:
    - "追踪"
    - "诊断"
    - "查错"
    - "为什么报错"
    - "哪里出了问题"
    - "查找原因"
    - "trace"
    - "diagnose"
    - "investigate"
    - "root cause analysis"
    - "logic chain"
    - "call stack"
    - "stack trace"
    - "error cause"
    - "cross verify"
    - "官方文档"
    - "official documentation"
    - "handoff report"
  medium_confidence:
    - "报错"
    - "error"
    - "crash"
    - "异常"
    - "exception"
    - "不正常"
    - "出了问题"
    - "null pointer"
    - "空指针"
    - "超时"
    - "timeout"
    - "OOM"
    - "死锁"
    - "不执行"
    - "性能"
    - "regression"
    - "响应时间"
    - "间歇性"
    - "逻辑"
  requires_context:
    - "逻辑" → only when context involves tracing code execution paths (not reading code for understanding)
    - "分析" → only when context involves error diagnosis (not code review or refactoring analysis)
negative_keywords:
  - "修复"
  - "fix"
  - "修掉"
  - "解决"
  - "处理一下"
  - "patch"
  - "直接改"
  - "帮我改"
  - "帮我修"
  - "帮我fix"
  - "紧急修复"
  - "修好"
tools:
  - name: logic_tracer
    script: "scripts/logic_tracer.py"
    parameters:
      error_desc: "The description of the error to trace."
      log_file: "Optional path to log file."
      source_code_context: "Optional source code snippet."
  - name: web_doc_fetcher
    script: "scripts/web_doc_fetcher.py"
    parameters:
      url: "The URL of the official documentation to fetch."
  - name: cross_verifier
    script: "scripts/cross_verifier.py"
    parameters:
      local: "Local logic implementation string or file path."
      spec: "Fetched official spec string."
  - name: security_auditor
    script: "scripts/security_auditor.py"
    parameters:
      target: "File path to scan, or raw code content."
      is_content: "Set true to treat target as raw code string."
---

# Investigation & Logic Tracing

## Workflow

1. Read error description and any available log files.
2. If source code context is provided, trace the business logic chain from entry point to failure point.
3. **Dual-Domain Verification**: If the logic involves external APIs, fetch and read the official web documentation. Compare the local implementation against the official spec.
4. **Anti-Auth Fallback**: If a URL is inaccessible (e.g., requires login/CAPTCHA):
   - *Plan C (Community Search)*: Search the web for community SDKs, forum posts, or blogs detailing the API implementation.
   - *Plan A (User Assist)*: If still stuck, politely ask the user to manually provide the document content (copy-paste or local file).
5. Classify the error: syntax-level, logic-gap, dependency-missing, or architecture-flaw.
6. Generate a structured handoff report containing:
   - Logic chain (how the code was intended to work)
   - Root cause (why it fails)
   - Recommended skill and action for downstream execution

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/logic_tracer.py` | Trace error through code context | `error_desc`, `log_file`(opt), `source_code_context`(opt) | Structured handoff report |
| `scripts/file_inspector.py` | Read file contents for analysis | `filepath` | File content string |
| `scripts/global_scanner.py` | Regex search across directory | `directory`, `pattern` | Match results list |

## Rules

- Never modify code. Output is always a report, never a file write.
- Handoff report must include `[recommended_skill]` field for downstream routing.
- If root cause is unclear, state what additional context is needed rather than guessing.
- When multiple error sources are possible, list all with confidence levels.

## Handoff Report Format

```
[logic_chain]: How the code was designed to work
[root_cause]: Why it fails
[recommended_skill]: Which skill should handle the fix
[action]: Specific action for the downstream skill
```
