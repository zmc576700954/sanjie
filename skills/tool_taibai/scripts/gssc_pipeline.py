"""
Four-step GSSC pipeline orchestrator.

GSSC = Gather -> Select -> Structure -> Compress
"""

from skills.tool_taibai.scripts.gather import gather_sources
from skills.tool_taibai.scripts.select import select_content
from skills.tool_taibai.scripts.structure import structure_document
from skills.tool_taibai.scripts.context_compressor import ContextCompressor


def run_pipeline(
    source_paths: list[str],
    doc_type: str = "spec",
    aggressive_compress: bool = False,
    output_path: str = None,
    author: str = "taibai",
) -> dict:
    """
    Run the full GSSC pipeline on the given source paths.

    Args:
        source_paths: List of file or directory paths to process.
        doc_type: Document type for structuring ("spec", "archive", "handoff", "memory").
        aggressive_compress: Whether to enable aggressive compression.
        output_path: Optional path to write the final compressed output.
        author: Author name to inject into document frontmatter.

    Returns:
        A dict with output_path, original_tokens, final_tokens, and compression_ratio.
    """
    # Step 1: Gather
    gathered = gather_sources(source_paths)

    # Step 2: Select
    selected = select_content(gathered)

    # Step 3: Structure
    structured = structure_document(selected, doc_type=doc_type, author=author)

    # Step 4: Compress
    compressor = ContextCompressor(aggressive=aggressive_compress)
    compressed = compressor.compress(structured)

    # Write to file if output_path provided
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(compressed)

    original_tokens = gathered["estimated_tokens"]
    final_tokens = len(compressed.split())
    compression_ratio = round(original_tokens / max(final_tokens, 1), 2)

    return {
        "output_path": output_path,
        "original_tokens": original_tokens,
        "final_tokens": final_tokens,
        "compression_ratio": compression_ratio,
    }
