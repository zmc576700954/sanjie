import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_taibai.scripts.archive_manager import archive_file
from skills.tool_taibai.scripts.context_compressor import ContextCompressor
from skills.utils import ensure_safe_path

mcp = FastMCP("Taibai Memory Manager")

@mcp.tool()
def compress_context(
    filepath: str = Field(description="Path to the verbose document or log file."),
    aggressive: bool = Field(default=False, description="If true, strips stop-words and comments aggressively.")
) -> str:
    """
    Compresses a verbose document or log file to reduce AI token load.
    It heuristically removes whitespace, HTML tags, minifies JSON, and truncates long stack traces.
    """
    try:
        safe_path = ensure_safe_path(filepath)
    except McpError as e:
        raise e
        
    if not os.path.exists(safe_path):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"File not found at {safe_path}"))
        
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        compressor = ContextCompressor(aggressive=aggressive)
        return compressor.compress(content)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Error compressing file: {e}"))

@mcp.tool()
def archive_document(
    filepath: str = Field(description="The path to the file to archive."),
    topic: str = Field(description="A short phrase describing the topic of the document."),
    summary: str = Field(description="A one-sentence summary of the document for the memory index.")
) -> str:
    """
    Archives a completed or deprecated document, moving it to cold storage and updating the hot index.
    """
    try:
        safe_path = ensure_safe_path(filepath)
        docs_root = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')), "docs")
        
        success = archive_file(safe_path, topic, summary, docs_root)
        if success:
            return f"Successfully archived {filepath} under topic '{topic}'."
        else:
             raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to archive. Ensure the file exists."))
    except Exception as e:
         raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

if __name__ == "__main__":
    mcp.run()
