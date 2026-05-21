---
name: wanglingguan
description: >
  Compliance, auditing, and security scanning toolset. Use this to verify if generated documents,
  agent outputs, and code adhere to Celestial Architecture standards. Provides multi-layer review:
  format compliance, quality assessment, assertion verification, and closed-loop ticket tracking.
tools:
  - name: format_auditor
    script: "scripts/format_auditor.py"
    parameters:
      file: "Path to the file to audit."
      type: "'document' (checks for YAML frontmatter) or 'handoff' (checks for A2A_ENVELOPE json)."
  - name: code_caller_tracer
    script: "scripts/code_caller_tracer.py"
    parameters:
      project: "Project root directory."
      class: "Target class name (for callers mode)."
      method: "Target method name."
      file: "File path (for null_check mode)."
      line: "Line number (for null_check mode)."
      mode: "'callers' or 'null_check'."
  - name: import_validator
    script: "scripts/import_validator.py"
    parameters:
      project: "Project root directory."
      mode: "'imports', 'validate_diagram', or 'verify_arrow'."
      file: "File to analyze (for imports mode)."
      from: "Source component (for verify_arrow mode)."
      to: "Target component (for verify_arrow mode)."
  - name: semantic_analyzer
    script: "scripts/semantic_analyzer.py"
    description: "AST-based code analysis for Python. Provides call graph, data flow, complexity, and dependency analysis."
    parameters:
      command: "'call_graph', 'dependencies', 'complexity', 'data_flow', or 'dead_code'."
      project: "Project root (for call_graph, data_flow, dead_code)."
      file: "File path (for dependencies, complexity)."
      method: "Target method (for call_graph)."
      source: "Source pattern (for data_flow)."
      sink: "Sink pattern (for data_flow)."
      entry_points: "Entry point files (for dead_code)."
      indirect: "Include indirect calls (for call_graph)."
  - name: security_scanner
    script: "scripts/security_scanner.py"
    description: "Lightweight security pattern scanner. Detects secrets, SQL injection, XSS, and misconfigurations."
    parameters:
      command: "'secrets', 'sql_injection', 'xss', 'misconfig', 'dangerous_ops', or 'all'."
      file: "File to scan (for file-based scans)."
      content: "Content string to scan (for dangerous_ops)."
  - name: ticket_manager
    script: "scripts/ticket_manager.py"
    description: "Review ticket CRUD operations. Creates and tracks ticket lifecycle from open to verified."
---

# Compliance, Auditing & Security Scanning

You have access to the Wang Lingguan multi-layer review toolset.

## Layer 1: Format Compliance
Use `format_auditor` to mechanically verify:
- YAML Frontmatter presence and required fields (title, date, status)
- A2A_ENVELOPE JSON block validity with target_agent

## Layer 2: Quality Assessment
Use `semantic_analyzer` with `complexity` command to flag:
- Functions with cyclomatic complexity > 10 (Warning)
- Functions with cyclomatic complexity > 20 (High)

## Layer 3: Assertion Verification
Use these tools for mechanical deep verification:

### Call Graph Analysis
- `semantic_analyzer call_graph` — Find all call sites of a method/function via AST
- More precise than regex; handles indirect calls with `--indirect`

### Data Flow Tracking
- `semantic_analyzer data_flow --source request,input --sink eval,exec`
- Traces sensitive data from entry points to dangerous sinks
- Use for INFO_EXPOSURE and DATA_FLOW assertion verification

### Security Scanning
- `security_scanner all --file path.py` — Run all security scans
- Detects: hardcoded secrets (entropy + pattern), SQL injection, XSS, misconfigurations
- Use for INPUT_VALIDATION, AUTH_BOUNDARY, CONFIG_SAFE assertions

## Layer 3.5: Closed-Loop Review Tickets
When findings are discovered, create tickets to track fixes:

1. **Create Ticket**: Use MCP `create_review_ticket` tool
   - Provide: target_agent, assertion_type, severity, description, fix_suggestion
   - Ticket ID format: WLG-YYYYMMDD-NNN
   - Stored at: `a2a_inbox/review_tickets/{ticket_id}.json`

2. **Monitor Status**: Use MCP `get_review_ticket_status` to check progress
   - States: open → pending → verified | reopened

3. **Verify Fix**: Use MCP `verify_fix` after agent submits fix
   - Verification types: security_scan, complexity_check, format_check, null_handling
   - Automatically updates ticket to verified or reopened

4. **Aggregate View**: Use MCP `get_review_summary` for project-wide ticket statistics

## No Centralization Rule
Tools detect issues. The reviewed agent is responsible for fixing them.
Never write Python wrappers to compensate for another agent's output errors.
