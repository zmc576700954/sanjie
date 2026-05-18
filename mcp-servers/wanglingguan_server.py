import os
import sys
import json
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_wanglingguan.scripts.format_auditor import audit_content
from skills.mcp_servers.utils import ensure_safe_path

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
            # Explicitly raise McpError so the LLM knows it messed up the format
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
    """Audits a Markdown document to ensure it complies with the Celestial Documentation Guard standards."""
    return _read_and_audit(filepath, 'document')

@mcp.tool()
def audit_handoff(
    filepath: str = Field(description="Absolute path to the agent output file to audit for JSON A2A_HANDOFF block.")
) -> str:
    """Audits a log or output file to ensure it complies with the A2A Text-Based Handoff Protocol."""
    return _read_and_audit(filepath, 'handoff')

if __name__ == "__main__":
    mcp.run()
