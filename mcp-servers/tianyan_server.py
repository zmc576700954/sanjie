import logging
import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_tianyan.scripts.logic_tracer import trace_error
from skills.tool_tianyan.scripts.web_doc_fetcher import fetch_doc
from skills.tool_tianyan.scripts.cross_verifier import verify_logic
from skills.utils import ensure_safe_path

logger = logging.getLogger(__name__)
mcp = FastMCP("TianYan Investigation Server")

@mcp.tool()
def logic_tracer(
    error_desc: str = Field(description="The description of the error or bug to investigate."),
    log_file: str = Field(default=None, description="Optional path to a log file. Must be within workspace."),
    source_code_context: str = Field(default="", description="Optional string containing relevant source code snippets.")
) -> str:
    """Analyzes an error description and local source context to trace business logic."""
    logger.info("Tracing logic...")
    try:
        safe_log = ensure_safe_path(log_file) if log_file else None
        return trace_error(error_desc, safe_log, source_code_context)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def web_doc_fetcher(
    url: str = Field(description="The URL of the official documentation to fetch via HTTP.")
) -> str:
    """
    Fetches external documentation from a URL.
    Returns ERROR_AUTH_BLOCKED if an auth wall is hit.
    """
    logger.info("Fetching URL: %s...", url)
    try:
        return fetch_doc(url)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def cross_verifier(
    local_logic: str = Field(description="A summary or string representation of the local code logic."),
    official_spec: str = Field(description="The text of the official specification.")
) -> str:
    """Cross-verifies local implementation logic against official specifications."""
    try:
        return verify_logic(local_logic, official_spec)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

if __name__ == "__main__":
    mcp.run()
