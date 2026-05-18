import os
import sys
from typing import List
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_kaishan.scripts.bulk_operations import bulk_delete, global_replace
from skills.tool_kaishan.scripts.blast_assessor import assess_blast_radius
from skills.mcp_servers.utils import ensure_safe_path

mcp = FastMCP("Kaishan Bulk Operations Server")

@mcp.tool()
def kaishan_bulk_delete(
    affected_files: List[str] = Field(description="List of file paths to be bulk deleted. Very dangerous.")
) -> str:
    """Bulk delete a list of files."""
    mcp.info(f"Bulk deleting {len(affected_files)} files...")
    try:
        safe_files = [ensure_safe_path(f) for f in affected_files]
        return bulk_delete(safe_files)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def kaishan_global_replace(
    affected_files: List[str] = Field(description="List of files to apply regex replacement to."),
    old_pattern: str = Field(description="The regex pattern to find."),
    new_str: str = Field(description="The replacement string.")
) -> str:
    """Perform a global regex replace across multiple files."""
    mcp.info(f"Replacing pattern across {len(affected_files)} files...")
    try:
        safe_files = [ensure_safe_path(f) for f in affected_files]
        return global_replace(safe_files, old_pattern, new_str)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def kaishan_assess_blast_radius(
    directory: str = Field(description="The root directory to assess."),
    pattern: str = Field(description="Regex pattern representing the planned changes."),
    action_type: str = Field(default="DELETE", description="Type of destructive action (e.g. DELETE, REPLACE)."),
    auto_approve: bool = Field(default=False, description="Auto-approve without checking.")
) -> dict:
    """Assess the blast radius of a bulk operation."""
    try:
        safe_dir = ensure_safe_path(directory)
        return assess_blast_radius(safe_dir, pattern, action_type, auto_approve)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

if __name__ == "__main__":
    mcp.run()
