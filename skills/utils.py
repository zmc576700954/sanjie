import os
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INVALID_PARAMS


def ensure_safe_path(filepath: str, workspace_root: str | None = None) -> str:
    """
    Resolves the absolute path and ensures it lies within the workspace root.
    Raises an McpError if the path is malicious or invalid.
    """
    if not workspace_root:
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))

    abs_path = os.path.abspath(filepath)
    abs_root = os.path.abspath(workspace_root)

    try:
        if not os.path.commonpath([abs_path, abs_root]) == abs_root:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message=f"Path traversal detected or path outside workspace: {filepath}"
                )
            )
    except ValueError:
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS,
                message=f"Path traversal detected or path outside workspace: {filepath}"
            )
        )
    return abs_path
