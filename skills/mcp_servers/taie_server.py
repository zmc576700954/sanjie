import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_taie.scripts.standard_write import write_with_validation
from skills.tool_taie.scripts.risk_assessor import assess_risk
from skills.mcp_servers.utils import ensure_safe_path

mcp = FastMCP("Taie Standard Write Server")

@mcp.tool()
def taie_write_with_validation(
    filepath: str = Field(description="The path to the file to overwrite."),
    content: str = Field(description="The full new file content to write.")
) -> str:
    """Write file content with syntax and AST regression checks."""
    mcp.info(f"Validating and writing to {filepath}...")
    try:
        safe_path = ensure_safe_path(filepath)
        return write_with_validation(safe_path, content)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def taie_assess_risk(
    target_file: str = Field(description="Path to the file being modified."),
    proposed_changes: str = Field(description="String describing the changes for risk evaluation."),
    auto_approve: bool = Field(default=False, description="Automatically approve without human input.")
) -> dict:
    """Evaluate modification risk and request user approval."""
    try:
        safe_path = ensure_safe_path(target_file)
        return assess_risk(safe_path, proposed_changes, auto_approve)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

if __name__ == "__main__":
    mcp.run()
