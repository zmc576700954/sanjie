"""
Gather step of the GSSC pipeline.
Collects source files and their metadata for context processing.
"""

import glob
import os


def gather_sources(paths: list[str], patterns: list[str] = None) -> dict:
    """
    Gather source files from the given paths.

    Args:
        paths: List of file paths or directory paths.
        patterns: Optional list of glob patterns to match files within directories.

    Returns:
        A dict with sources, total_size_bytes, and estimated_tokens.
    """
    sources = []
    total_size_bytes = 0
    total_content = ""

    for path in paths:
        if os.path.isfile(path):
            # Single file
            content = _read_file(path)
            if content is not None:
                size_bytes = len(content.encode("utf-8"))
                total_size_bytes += size_bytes
                total_content += content + " "
                sources.append({
                    "path": path,
                    "type": "file",
                    "size_bytes": size_bytes,
                    "content_preview": _make_preview(content),
                })
        elif os.path.isdir(path):
            # Directory: collect matching files
            if patterns:
                file_set = set()
                for pattern in patterns:
                    matched = glob.glob(os.path.join(path, "**", pattern), recursive=True)
                    for f in matched:
                        if os.path.isfile(f):
                            file_set.add(f)
                files_to_process = sorted(file_set)
            else:
                files_to_process = []
                for root, _dirs, files in os.walk(path):
                    for fname in files:
                        files_to_process.append(os.path.join(root, fname))

            for fpath in files_to_process:
                content = _read_file(fpath)
                if content is not None:
                    size_bytes = len(content.encode("utf-8"))
                    total_size_bytes += size_bytes
                    total_content += content + " "
                    sources.append({
                        "path": fpath,
                        "type": "file",
                        "size_bytes": size_bytes,
                        "content_preview": _make_preview(content),
                    })

    # Heuristic token estimation: ~4 characters per token on average
    # (works better than word count for mixed code/text/Chinese content)
    estimated_tokens = max(1, len(total_content) // 4)

    return {
        "sources": sources,
        "total_size_bytes": total_size_bytes,
        "estimated_tokens": estimated_tokens,
    }


def _read_file(path: str) -> str | None:
    """Read a file as UTF-8 text, returning None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _make_preview(content: str, max_len: int = 200) -> str:
    """Return the first max_len characters, or the full content if shorter."""
    if len(content) <= max_len:
        return content
    return content[:max_len]
