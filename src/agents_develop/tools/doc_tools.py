"""Wrappers for documentation tools from skills/."""
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from skills.tool_taibai.scripts.context_compressor import ContextCompressor
from skills.tool_taibai.scripts.gssc_pipeline import run_pipeline


def compress_context(file_path: str, aggressive: bool = False) -> str:
    """Compress a verbose document to reduce token load."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        compressor = ContextCompressor(aggressive=aggressive)
        return compressor.compress(content)
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error compressing: {e}"


def run_gssc_pipeline(
    source_paths: list[str],
    doc_type: str = "spec",
    aggressive_compress: bool = False,
    output_path: str = None,
) -> dict:
    """Run the GSSC pipeline: Gather, Select, Structure, Compress."""
    return run_pipeline(
        source_paths=source_paths,
        doc_type=doc_type,
        aggressive_compress=aggressive_compress,
        output_path=output_path,
    )
