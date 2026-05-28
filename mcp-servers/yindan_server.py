import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_yindan.scripts.precise_fix import precise_replace

mcp = FastMCP("Yindan Precision Fix")


@mcp.tool()
def precise_fix(
    filepath: str = Field(description="Target file path."),
    old_str: str = Field(description="Exact text to find and replace (non-empty)."),
    new_str: str = Field(description="Replacement text (can be empty for deletion)."),
) -> str:
    """
    Perform a precise, single-occurrence text replacement in a file with
    validation and automatic rollback on failure.

    - Only replaces the first occurrence of old_str.
    - For .py files, runs py_compile syntax check after replacement.
    - Rolls back to original content if any validation fails.
    - Rejects empty old_str, non-string parameters, and overly large files (>100 MB).
    """
    result = precise_replace(filepath, old_str, new_str)

    if result.startswith("Error:"):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=result))

    return result


if __name__ == "__main__":
    mcp.run()
