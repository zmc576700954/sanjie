"""
Four-step GSSC pipeline orchestrator.

GSSC = Gather -> Select -> Structure -> Compress
"""

import logging

from skills.tool_taibai.scripts.gather import gather_sources, _estimate_tokens
from skills.tool_taibai.scripts.select import select_content
from skills.tool_taibai.scripts.structure import structure_document
from skills.tool_taibai.scripts.context_compressor import ContextCompressor

logger = logging.getLogger("taibai.pipeline")


def run_pipeline(
    source_paths: list[str],
    doc_type: str = "spec",
    aggressive_compress: bool = False,
    output_path: str | None = None,
    author: str = "taibai",
    noise_patterns: list[str] = None,
    select_config_path: str = None,
) -> dict:
    """
    Run the full GSSC pipeline on the given source paths.

    Args:
        source_paths: List of file or directory paths to process.
        doc_type: Document type for structuring ("spec", "archive", "handoff", "memory").
        aggressive_compress: Whether to enable aggressive compression.
        output_path: Optional path to write the final compressed output.
        author: Author name to inject into document frontmatter.
        noise_patterns: Optional custom noise patterns for select step.
        select_config_path: Optional path to a JSON/YAML config for select patterns.

    Returns:
        A dict with output_path, original_tokens, final_tokens, compression_ratio,
        and any warnings collected during processing.
    """
    warnings = []

    # Step 1: Gather
    gathered = gather_sources(source_paths)
    if not gathered["sources"]:
        warnings.append("No readable source files found")
        logger.warning("No readable source files found for paths: %s", source_paths)
    if "warnings" in gathered:
        warnings.extend(gathered["warnings"])

    # Step 2: Select
    selected = select_content(
        gathered,
        noise_patterns=noise_patterns,
        config_path=select_config_path,
    )

    # Step 3: Structure
    structured = structure_document(selected, doc_type=doc_type, author=author)

    # Step 4: Compress
    compressor = ContextCompressor(aggressive=aggressive_compress)
    compressed = compressor.compress(structured)

    # Write to file if output_path provided
    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(compressed)
        except OSError as e:
            warnings.append(f"Failed to write output: {e}")
            logger.error("Failed to write output to %s: %s", output_path, e)

    original_tokens = gathered["estimated_tokens"]
    final_tokens = _estimate_tokens(compressed)
    compression_ratio = round(original_tokens / max(final_tokens, 1), 2)

    result = {
        "output_path": output_path,
        "original_tokens": original_tokens,
        "final_tokens": final_tokens,
        "compression_ratio": compression_ratio,
    }
    if warnings:
        result["warnings"] = warnings
    return result
