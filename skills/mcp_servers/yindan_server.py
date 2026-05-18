import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_yindan.scripts.precise_fix import precise_replace
from skills.mcp_servers.utils import ensure_safe_path

mcp = FastMCP("Yindan Precise Fix Server")

@mcp.tool()
def yindan_precise_replace(
    filepath: str = Field(description="The absolute or relative path to the file to be modified."),
    old_str: str = Field(description="The EXACT literal text to find and replace. Must match the target file exactly, including whitespace and indentation. Do not guess."),
    new_str: str = Field(description="The new literal text to insert in place of old_str.")
) -> str:
    """
    Replace exact literal text in a file with regression validation and rollback.
    """
    
    try:
        safe_path = ensure_safe_path(filepath)
    except McpError as e:
        raise e
        
    try:
        result = precise_replace(safe_path, old_str, new_str)
        if "Error" in result:
             raise McpError(ErrorData(code=INTERNAL_ERROR, message=result))
        return result
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to execute precise_replace: {e}"))

if __name__ == "__main__":
    mcp.run()
