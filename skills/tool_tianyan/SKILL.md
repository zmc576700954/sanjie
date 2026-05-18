---
name: tianyan
description: >
  Use when investigating bugs, tracing business logic, diagnosing errors,
  or searching technical documentation. Handles deep root-cause analysis,
  logic chain tracing, and multi-source doc queries with cross-verification.
  Do NOT use for code modification — investigation only.
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
