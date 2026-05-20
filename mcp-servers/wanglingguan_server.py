import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_wanglingguan.scripts.format_auditor import audit_content
from skills.tool_wanglingguan.scripts.code_caller_tracer import find_callers, check_null_handling
from skills.tool_wanglingguan.scripts.import_validator import verify_dependency_direction
from skills.utils import ensure_safe_path

mcp = FastMCP("Wang Lingguan Auditor")


def _read_and_audit(filepath: str, check_type: str) -> str:
    try:
        safe_path = ensure_safe_path(filepath)
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

    except McpError as e:
        raise e
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
        safe_root = ensure_safe_path(project_root)
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
        safe_path = ensure_safe_path(file_path)
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
        safe_root = ensure_safe_path(project_root)
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


if __name__ == "__main__":
    mcp.run()
