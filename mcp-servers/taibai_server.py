import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_taibai.scripts.archive_manager import archive_file
from skills.tool_taibai.scripts.context_compressor import ContextCompressor
from skills.tool_taibai.scripts.gather import gather_sources
from skills.tool_taibai.scripts.select import select_content
from skills.tool_taibai.scripts.structure import structure_document
from skills.tool_taibai.scripts.gssc_pipeline import run_pipeline
from skills.tool_taibai.scripts.review_request import request_review
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
        docs_root = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), "docs")
        
        success = archive_file(safe_path, topic, summary, docs_root)
        if success:
            return f"Successfully archived {filepath} under topic '{topic}'."
        else:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to archive. Ensure the file exists."))
    except Exception as e:
         raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def gather_sources_tool(
    source_paths: list[str] = Field(description="List of file or directory paths to collect."),
    patterns: list[str] = Field(default=None, description="Optional list of glob patterns to match files within directories.")
) -> dict:
    """Gather source files and their metadata for context processing."""
    return gather_sources(paths=source_paths, patterns=patterns)

@mcp.tool()
def select_content_tool(
    raw_sources: dict = Field(description="Output dict from gather_sources, containing a 'sources' list."),
    noise_patterns: list[str] = Field(default=None, description="Optional list of regex patterns to override default noise filters."),
    keep_sections: list[str] = Field(default=None, description="Optional list of section names to preserve.")
) -> dict:
    """Filter out noise lines from gathered source content."""
    return select_content(raw_sources=raw_sources, noise_patterns=noise_patterns, keep_sections=keep_sections)

@mcp.tool()
def structure_document_tool(
    selected_sources: dict = Field(description="Output dict from select_content, containing 'filtered_sources'."),
    doc_type: str = Field(default="spec", description="Document type: 'spec', 'archive', 'handoff', or 'memory'."),
    author: str = Field(default="taibai", description="Author name to inject into YAML frontmatter."),
    metadata: dict = Field(default=None, description="Optional dict of additional frontmatter fields.")
) -> str:
    """Structure a document with YAML frontmatter and Markdown sections."""
    return structure_document(selected_sources=selected_sources, doc_type=doc_type, author=author, metadata=metadata)

@mcp.tool()
def run_gssc_pipeline_tool(
    source_paths: list[str] = Field(description="List of file or directory paths to process."),
    doc_type: str = Field(default="spec", description="Document type for structuring."),
    aggressive_compress: bool = Field(default=False, description="Whether to enable aggressive compression."),
    output_path: str = Field(default=None, description="Optional path to write the final compressed output."),
    author: str = Field(default="taibai", description="Author name for frontmatter.")
) -> dict:
    """Run the full GSSC pipeline: Gather -> Select -> Structure -> Compress."""
    return run_pipeline(
        source_paths=source_paths,
        doc_type=doc_type,
        aggressive_compress=aggressive_compress,
        output_path=output_path,
        author=author,
    )

@mcp.tool()
def request_review_tool(
    document_path: str = Field(description="Path to the document to review."),
    review_type: str = Field(default="format", description="Category of review: 'format', 'quality', 'assertion', or 'architecture'."),
    context_notes: str = Field(default="", description="Optional additional context for the reviewer.")
) -> dict:
    """Submit a document for review. The scheduler assigns the review to a capable agent."""
    return request_review(document_path=document_path, review_type=review_type, context_notes=context_notes)

if __name__ == "__main__":
    mcp.run()
