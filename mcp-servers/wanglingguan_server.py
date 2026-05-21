import os
import sys
from typing import List, Optional

from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

# JSON-RPC internal error code (used when MCP library doesn't provide the constant)
INTERNAL_ERROR = -32603

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_wanglingguan.scripts.format_auditor import audit_content
from skills.tool_wanglingguan.scripts.code_caller_tracer import find_callers, check_null_handling
from skills.tool_wanglingguan.scripts.import_validator import verify_dependency_direction
from skills.tool_wanglingguan.scripts.semantic_analyzer import (
    analyze_call_graph as semantic_analyze_call_graph,
    trace_data_flow as semantic_trace_data_flow,
    detect_complexity as semantic_detect_complexity,
)
from skills.tool_wanglingguan.scripts.security_scanner import (
    scan_secrets,
    scan_sql_injection,
    scan_xss_vectors,
    scan_misconfiguration,
)
from skills.tool_wanglingguan.scripts.ticket_manager import (
    create_ticket,
    get_ticket,
    update_ticket_status,
    list_tickets,
    get_ticket_summary,
)
mcp = FastMCP("Wang Lingguan Auditor")


def _ensure_safe_path(filepath: str) -> str:
    """Resolves the absolute path and ensures it lies within the workspace root."""
    abs_path = os.path.abspath(filepath)
    abs_root = os.path.abspath(project_root)

    try:
        if not os.path.commonpath([abs_path, abs_root]) == abs_root:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Path traversal detected or path outside workspace: {filepath}"
                )
            )
    except ValueError:
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"Path traversal detected or path outside workspace: {filepath}"
            )
        )
    return abs_path


def _read_and_audit(filepath: str, check_type: str) -> str:
    try:
        safe_path = _ensure_safe_path(filepath)
    except McpError as e:
        raise e

    if not os.path.exists(safe_path):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"File not found at {safe_path}"))

    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        result = audit_content(content, check_type)

        report = []
        report.append(f"=== WANG LINGGUAN AUDIT REPORT ===")
        report.append(f"Target: {filepath}")
        report.append(f"Audit Type: {check_type.upper()}")
        report.append(f"Status: {result['status']}")

        if result['errors']:
            report.append("Violations:")
            for err in result['errors']:
                report.append(f" - {err}")

        report.append("==================================")

        if result['status'] == 'FAIL':
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="\n".join(report)))

        return "\n".join(report)

    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error auditing file: {e}"))


@mcp.tool()
def audit_document(
    filepath: str = Field(description="Absolute path to the document file to audit for YAML Frontmatter.")
) -> str:
    """Layer 1: Audits a Markdown document to ensure it complies with the Celestial Documentation Guard standards (YAML Frontmatter)."""
    return _read_and_audit(filepath, 'document')


@mcp.tool()
def audit_handoff(
    filepath: str = Field(description="Absolute path to the agent output file to audit for JSON A2A_ENVELOPE block.")
) -> str:
    """Layer 1: Audits a log or output file to ensure it complies with the A2A Text-Based Handoff Protocol."""
    return _read_and_audit(filepath, 'handoff')


@mcp.tool()
def trace_callers(
    project_root: str = Field(description="Project root directory to search within."),
    target_class: str = Field(description="Class name to find call sites for (e.g., 'BaseEnhancedFileUpload')."),
    target_method: str = Field(description="Method name to find call sites for (e.g., 'getBucket').")
) -> str:
    """Layer 3: Finds all call sites of a specific class::method. Use this to verify NULL_PATH boundary checks — trace who calls the method and whether they handle null returns."""
    try:
        safe_root = _ensure_safe_path(project_root)
        callers = find_callers(safe_root, target_class, target_method)

        report = []
        report.append(f"=== CALLER TRACE REPORT ===")
        report.append(f"Target: {target_class}::{target_method}")
        report.append(f"Call sites found: {len(callers)}")
        for c in callers:
            report.append(f"\nFile: {c['file']}:{c['line']}")
            report.append(f"  Context: {c['context']}")
        report.append("===========================")

        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error tracing callers: {e}"))


@mcp.tool()
def verify_null_handling(
    project_root: str = Field(description="Project root directory for context."),
    file_path: str = Field(description="Absolute path to the file containing the function."),
    line_number: int = Field(description="Line number of the function/method to check null handling for.")
) -> str:
    """Layer 3: Checks if a function has explicit null/empty handling. Use this to verify NULL_PATH boundary assertions — confirms whether callers safely handle potential null returns."""
    try:
        safe_path = _ensure_safe_path(file_path)
        result = check_null_handling(project_root, safe_path, line_number)

        report = []
        report.append(f"=== NULL HANDLING CHECK ===")
        report.append(f"File: {file_path}:{line_number}")
        report.append(f"Has null check: {'YES' if result['has_null_check'] else 'NO'}")
        if result.get('checks_found'):
            report.append("Checks found:")
            for check in result['checks_found']:
                report.append(f"  Line {check['line']}: {check['code']}")
        if result.get('error'):
            report.append(f"Error: {result['error']}")
        report.append("===========================")

        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error checking null handling: {e}"))


@mcp.tool()
def verify_architecture_arrow(
    project_root: str = Field(description="Project root directory."),
    from_component: str = Field(description="Source component name (arrow origin)."),
    to_component: str = Field(description="Target component name (arrow destination).")
) -> str:
    """Layer 3: Verifies if an architecture diagram arrow direction is correct by checking code imports. If A imports B, the arrow A -> B is correct (A depends on B)."""
    try:
        safe_root = _ensure_safe_path(project_root)
        result = verify_dependency_direction(safe_root, from_component, to_component)

        report = []
        report.append(f"=== ARCHITECTURE ARROW VERIFICATION ===")
        report.append(f"Arrow: {result['from']} -> {result['to']}")
        report.append(f"Correct: {'YES' if result['arrow_correct'] else 'NO' if result['arrow_correct'] is False else 'UNKNOWN'}")
        for ev in result['evidence']:
            if isinstance(ev, dict):
                report.append(f"  Evidence: {ev['conclusion']}")
                report.append(f"    File: {ev['file']}:{ev['line']}")
            else:
                report.append(f"  {ev}")
        report.append("=======================================")

        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error verifying arrow: {e}"))


# ───────────────────────────────────────────────
# Phase 2: New Semantic & Security Tools
# ───────────────────────────────────────────────

@mcp.tool()
def analyze_call_graph(
    project_root: str = Field(description="Project root directory to search within."),
    target_method: str = Field(description="Method or function name to find call sites for (e.g., 'getBucket' or 'MyClass.method')."),
    include_indirect: bool = Field(default=False, description="If True, also finds indirect calls through variables.")
) -> str:
    """Layer 3 (AST): Analyzes call graph for a target method using AST. Finds indirect calls when include_indirect=True."""
    try:
        safe_root = _ensure_safe_path(project_root)
        result = semantic_analyze_call_graph(safe_root, target_method, include_indirect)

        report = []
        report.append(f"=== AST CALL GRAPH ANALYSIS ===")
        report.append(f"Target: {result['target_method']}")
        report.append(f"Call sites found: {result['call_sites_found']}")
        for site in result['call_sites']:
            report.append(f"\nFile: {site['file']}:{site['line']}")
            report.append(f"  Context: {site['context']}")
            report.append(f"  Type: {site['call_type']}")
            if site.get('in_function'):
                report.append(f"  In function: {site['in_function']}")
            if site.get('in_class'):
                report.append(f"  In class: {site['in_class']}")
        report.append("================================")

        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error analyzing call graph: {e}"))


@mcp.tool()
def trace_data_flow(
    project_root: str = Field(description="Project root directory."),
    source_pattern: str = Field(description="Variable or function name marking a data source (e.g., 'request,input')."),
    sink_pattern: str = Field(description="Function name marking a dangerous sink (e.g., 'eval,exec,os.system').")
) -> str:
    """Layer 3 (Security): Traces sensitive data flow from source to sink. Use for INFO_EXPOSURE and INPUT_VALIDATION verification."""
    try:
        safe_root = _ensure_safe_path(project_root)
        flows = semantic_trace_data_flow(safe_root, source_pattern, sink_pattern)

        report = []
        report.append(f"=== DATA FLOW TRACE ===")
        report.append(f"Source: {source_pattern}")
        report.append(f"Sink: {sink_pattern}")
        report.append(f"Flows found: {len(flows)}")

        if not flows:
            report.append("No data flow paths found.")
        else:
            for flow in flows:
                report.append(f"\nFile: {flow['file']}")
                report.append(f"  Function: {flow['function']}")
                report.append(f"  Variable: {flow['variable']}")
                report.append(f"  Source (line {flow['source_line']}): {flow['source_type']}")
                report.append(f"  Sink (line {flow['sink_line']}): {flow['sink_type']}")
                if flow.get('is_propagated'):
                    report.append(f"  Note: Variable was propagated through assignment chain")

        report.append("=======================")
        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error tracing data flow: {e}"))


@mcp.tool()
def scan_security_patterns(
    file_path: str = Field(description="Absolute path to the file to scan."),
    scan_types: List[str] = Field(
        default=["secrets", "sql_injection", "xss", "misconfiguration"],
        description="List of scan types to run."
    )
) -> str:
    """Layer 3 (Security): Scans file for security pattern violations. Configurable scan type list."""
    try:
        safe_path = _ensure_safe_path(file_path)
        all_findings = []

        if "secrets" in scan_types:
            all_findings.extend(scan_secrets(safe_path))
        if "sql_injection" in scan_types:
            all_findings.extend(scan_sql_injection(safe_path))
        if "xss" in scan_types:
            all_findings.extend(scan_xss_vectors(safe_path))
        if "misconfiguration" in scan_types:
            all_findings.extend(scan_misconfiguration(safe_path))

        # Filter out error entries
        findings = [f for f in all_findings if 'error' not in f]
        errors = [f for f in all_findings if 'error' in f]

        report = []
        report.append(f"=== SECURITY SCAN REPORT ===")
        report.append(f"Target: {file_path}")
        report.append(f"Scan types: {', '.join(scan_types)}")
        report.append(f"Findings: {len(findings)}")

        if errors:
            report.append("\nErrors during scan:")
            for err in errors:
                report.append(f"  - {err['error']}")

        if findings:
            # Sort by severity
            severity_order = {'critical': 0, 'high': 1, 'warning': 2, 'note': 3}
            findings.sort(key=lambda f: severity_order.get(f.get('severity', 'note'), 99))

            for f in findings:
                subtype = f.get('subtype', '')
                report.append(f"\n[{f.get('severity', 'unknown').upper()}] {f.get('type', 'unknown')}")
                if subtype:
                    report.append(f"  Subtype: {subtype}")
                report.append(f"  Line {f.get('line', '?')}: {f.get('message', '')}")
                report.append(f"  Evidence: {f.get('evidence', 'N/A')}")
                if f.get('fix'):
                    report.append(f"  Fix: {f['fix']}")
        else:
            report.append("No security issues detected.")

        report.append("============================")
        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error scanning security patterns: {e}"))


@mcp.tool()
def check_complexity(
    file_path: str = Field(description="Absolute path to the Python file to analyze."),
    threshold: int = Field(default=10, description="Cyclomatic complexity threshold. Functions exceeding this are flagged.")
) -> str:
    """Layer 2 (Quality): Checks cyclomatic complexity per function. Flags functions exceeding threshold."""
    try:
        safe_path = _ensure_safe_path(file_path)
        result = semantic_detect_complexity(safe_path)

        if 'error' in result:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=result['error']))

        report = []
        report.append(f"=== COMPLEXITY CHECK ===")
        report.append(f"File: {file_path}")
        report.append(f"Total functions: {result['total_functions']}")
        report.append(f"Max complexity: {result['max_complexity']}")

        flagged = [f for f in result['functions'] if f['complexity'] > threshold]
        report.append(f"Functions exceeding threshold ({threshold}): {len(flagged)}")

        for func in result['functions']:
            flag = " *** EXCEEDS THRESHOLD ***" if func['complexity'] > threshold else ""
            report.append(f"\n  {func['name']} (line {func['line']}): complexity = {func['complexity']}{flag}")

        report.append("========================")
        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error checking complexity: {e}"))


@mcp.tool()
def detect_circular_dependencies(
    project_root: str = Field(description="Project root directory."),
    from_component: str = Field(description="Source component name."),
    to_component: str = Field(description="Target component name.")
) -> str:
    """Layer 3 (Architecture): Detects if two components have circular import dependencies."""
    try:
        safe_root = _ensure_safe_path(project_root)
        # Use import_validator to check both directions
        from_result = verify_dependency_direction(safe_root, from_component, to_component)
        to_result = verify_dependency_direction(safe_root, to_component, from_component)

        a_imports_b = from_result['arrow_correct'] is True
        b_imports_a = to_result['arrow_correct'] is True
        has_circular = a_imports_b and b_imports_a

        report = []
        report.append(f"=== CIRCULAR DEPENDENCY CHECK ===")
        report.append(f"Components: {from_component} <-> {to_component}")

        if a_imports_b:
            report.append(f"\n{from_component} -> {to_component}: DEPENDENCY FOUND")
        if b_imports_a:
            report.append(f"\n{to_component} -> {from_component}: DEPENDENCY FOUND")

        if has_circular:
            report.append(f"\n*** CIRCULAR DEPENDENCY DETECTED ***")
            report.append(f"Fix: Extract shared code into a third module, or refactor to eliminate the cycle.")
        else:
            report.append(f"\nNo circular dependency detected between these components.")

        report.append("=================================")
        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error detecting circular dependencies: {e}"))


@mcp.tool()
def verify_fix(
    original_finding_id: str = Field(description="ID of the original review ticket (e.g., WLG-20260521-001)."),
    fixed_file_path: str = Field(description="Absolute path to the fixed file to verify."),
    verification_type: str = Field(
        description="Type of verification to run. One of: security_scan, complexity_check, format_check, null_handling."
    )
) -> str:
    """Layer 3 (Closed Loop): Verifies a previously reported issue has been fixed. Returns verification result and updates ticket status."""
    try:
        safe_path = _ensure_safe_path(fixed_file_path)
        ticket = get_ticket(original_finding_id)

        if ticket is None:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Ticket not found: {original_finding_id}"))

        verification_result = {"ticket_id": original_finding_id, "checks_run": [], "passed": True}

        if verification_type == "security_scan":
            findings = scan_secrets(safe_path)
            findings += scan_sql_injection(safe_path)
            findings += scan_xss_vectors(safe_path)
            findings += scan_misconfiguration(safe_path)
            critical = [f for f in findings if f.get('severity') == 'critical']
            verification_result["checks_run"].append("security_scan")
            verification_result["findings_remaining"] = len(critical)
            verification_result["passed"] = len(critical) == 0

        elif verification_type == "complexity_check":
            result = semantic_detect_complexity(safe_path)
            verification_result["checks_run"].append("complexity_check")
            verification_result["max_complexity"] = result.get("max_complexity", 0)
            verification_result["passed"] = result.get("max_complexity", 0) <= 10

        elif verification_type == "format_check":
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            doc_result = audit_content(content, 'document')
            handoff_result = audit_content(content, 'handoff')
            verification_result["checks_run"].append("format_check")
            verification_result["document_pass"] = doc_result["status"] == "PASS"
            verification_result["handoff_pass"] = handoff_result["status"] == "PASS"
            verification_result["passed"] = doc_result["status"] == "PASS" and handoff_result["status"] == "PASS"

        elif verification_type == "null_handling":
            # Use existing null handling check - requires line number from ticket evidence
            line_number = ticket.get("evidence", {}).get("line", 0)
            if line_number:
                result = check_null_handling(os.path.dirname(safe_path), safe_path, line_number)
                verification_result["checks_run"].append("null_handling")
                verification_result["has_null_check"] = result.get("has_null_check", False)
                verification_result["passed"] = result.get("has_null_check", False)
            else:
                verification_result["passed"] = False
                verification_result["error"] = "No line number in ticket evidence"

        else:
            verification_result["passed"] = False
            verification_result["error"] = f"Unknown verification_type: {verification_type}"

        # Update ticket status
        new_status = "verified" if verification_result["passed"] else "reopened"
        update_ticket_status(
            original_finding_id,
            new_status,
            actor="wanglingguan",
            verification_result=verification_result,
        )

        report = []
        report.append(f"=== FIX VERIFICATION ===")
        report.append(f"Ticket: {original_finding_id}")
        report.append(f"Fixed file: {fixed_file_path}")
        report.append(f"Verification type: {verification_type}")
        report.append(f"Checks run: {', '.join(verification_result['checks_run'])}")
        report.append(f"Result: {'PASSED - Ticket verified' if verification_result['passed'] else 'FAILED - Ticket reopened'}")
        if not verification_result["passed"] and verification_result.get("error"):
            report.append(f"Error: {verification_result['error']}")
        report.append("========================")

        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error verifying fix: {e}"))


@mcp.tool()
def create_review_ticket(
    target_agent: str = Field(description="Name of the agent responsible for fixing the issue."),
    target_file: str = Field(description="File path where the issue was found."),
    assertion_type: str = Field(description="Type of assertion: NULL_PATH, INFO_EXPOSURE, REGISTRATION, INPUT_VALIDATION, AUTH_BOUNDARY, DATA_FLOW, CONFIG_SAFE."),
    severity: str = Field(description="Severity: Critical, High, Warning, Note, TODO."),
    description: str = Field(description="Human-readable description of the finding."),
    fix_suggestion: str = Field(description="Concrete fix suggestion with code reference."),
    due_date: Optional[str] = Field(default=None, description="Optional due date in ISO 8601 format."),
) -> str:
    """Layer 3.5 (Closed Loop): Creates a Review Ticket to track a finding from discovery through verification."""
    try:
        ticket_id = create_ticket(
            target_agent=target_agent,
            target_file=target_file,
            assertion_type=assertion_type,
            severity=severity,
            description=description,
            evidence={"file": target_file},
            fix_suggestion=fix_suggestion,
            due_date=due_date,
        )

        report = []
        report.append(f"=== REVIEW TICKET CREATED ===")
        report.append(f"Ticket ID: {ticket_id}")
        report.append(f"Target Agent: {target_agent}")
        report.append(f"Assertion Type: {assertion_type}")
        report.append(f"Severity: {severity}")
        report.append(f"Status: open")
        report.append(f"Fix Suggestion: {fix_suggestion}")
        if due_date:
            report.append(f"Due Date: {due_date}")
        report.append(f"\nTicket stored at: a2a_inbox/review_tickets/{ticket_id}.json")
        report.append("=============================")

        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error creating review ticket: {e}"))


@mcp.tool()
def get_review_ticket_status(
    ticket_id: str = Field(description="Ticket ID to query."),
) -> str:
    """Layer 3.5 (Closed Loop): Gets the current status of a review ticket."""
    try:
        ticket = get_ticket(ticket_id)
        if ticket is None:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Ticket not found: {ticket_id}"))

        report = []
        report.append(f"=== TICKET STATUS ===")
        report.append(f"Ticket ID: {ticket['ticket_id']}")
        report.append(f"Status: {ticket['status']}")
        report.append(f"Target Agent: {ticket['target_agent']}")
        report.append(f"Assertion Type: {ticket['assertion_type']}")
        report.append(f"Severity: {ticket['severity']}")
        report.append(f"Description: {ticket['description']}")
        report.append(f"Fix Suggestion: {ticket['fix_suggestion']}")
        if ticket.get('fixed_file'):
            report.append(f"Fixed File: {ticket['fixed_file']}")
        if ticket.get('verification_result'):
            report.append(f"Verification Result: {ticket['verification_result']}")

        report.append("\nStatus History:")
        for entry in ticket.get('status_history', []):
            report.append(f"  [{entry['timestamp']}] {entry['status']} by {entry['actor']}")

        report.append("=====================")
        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error getting ticket status: {e}"))


@mcp.tool()
def get_review_summary() -> str:
    """Layer 3.5 (Closed Loop): Gets aggregate statistics of all review tickets."""
    try:
        summary = get_ticket_summary()

        report = []
        report.append(f"=== REVIEW TICKET SUMMARY ===")
        report.append(f"Total tickets: {summary['total']}")
        report.append(f"By Status:")
        for status, count in summary['by_status'].items():
            report.append(f"  {status}: {count}")
        report.append(f"By Severity:")
        for severity, count in summary['by_severity'].items():
            report.append(f"  {severity}: {count}")
        if summary['open_tickets']:
            report.append(f"\nOpen Tickets:")
            for tid in summary['open_tickets']:
                report.append(f"  - {tid}")
        report.append("=============================")

        return "\n".join(report)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error getting review summary: {e}"))


if __name__ == "__main__":
    mcp.run()
