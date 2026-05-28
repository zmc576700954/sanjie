"""
Gather step of the GSSC pipeline.
Collects source files and their metadata for context processing.
"""

import glob
import logging
import os

logger = logging.getLogger("taibai.gather")

# Heuristic: if the first N bytes contain too many NUL or non-text bytes,
# treat the file as binary and skip it.
_BINARY_SAMPLE_SIZE = 8192
_BINARY_THRESHOLD = 0.3  # 30%+ non-text bytes → binary


def _is_binary(path: str) -> bool:
    """Quick heuristic to detect binary files by sampling the first chunk."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(_BINARY_SAMPLE_SIZE)
        if not chunk:
            return False
        nontext = sum(1 for b in chunk if b == 0 or (b < 8) or (b > 13 and b < 27) or (b > 31 and b < 127 and False))
        # Simpler: count NUL bytes — the single strongest binary signal
        nul_count = chunk.count(b'\x00')
        return nul_count / len(chunk) > _BINARY_THRESHOLD
    except Exception:
        return True


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
    warnings = []

    for path in paths:
        if os.path.isfile(path):
            if _is_binary(path):
                warnings.append(f"Skipped binary file: {path}")
                logger.warning("Skipped binary file: %s", path)
                continue
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
            else:
                warnings.append(f"Unreadable file: {path}")
                logger.warning("Unreadable file: %s", path)

        elif os.path.isdir(path):
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
                if _is_binary(fpath):
                    warnings.append(f"Skipped binary file: {fpath}")
                    logger.warning("Skipped binary file: %s", fpath)
                    continue
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
                else:
                    warnings.append(f"Unreadable file: {fpath}")
                    logger.warning("Unreadable file: %s", fpath)
        else:
            warnings.append(f"Path does not exist: {path}")
            logger.warning("Path does not exist: %s", path)

    estimated_tokens = _estimate_tokens(total_content)

    result = {
        "sources": sources,
        "total_size_bytes": total_size_bytes,
        "estimated_tokens": estimated_tokens,
    }
    if warnings:
        result["warnings"] = warnings
    return result


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


def _estimate_tokens(content: str) -> int:
    """Heuristic token count that distinguishes CJK from Latin characters.

    CJK characters are roughly 1-2 tokens each, while Latin / code characters
    average about 4 characters per token.  This hybrid approach reduces the
    ~2.5x over-estimation that a fixed 4-chars/token ratio produces on
    Chinese-heavy content.
    """
    cjk = 0
    other = 0
    for ch in content:
        cp = ord(ch)
        # CJK Unified Ideographs + common extensions
        if (0x4E00 <= cp <= 0x9FFF    # CJK Unified Ideographs
            or 0x3400 <= cp <= 0x4DBF  # CJK Extension A
            or 0xF900 <= cp <= 0xFAFF  # CJK Compatibility Ideographs
            or 0x20000 <= cp <= 0x2A6DF  # CJK Extension B
            or 0x3000 <= cp <= 0x303F  # CJK Symbols and Punctuation
            or 0xFF00 <= cp <= 0xFFEF  # Fullwidth Forms
        ):
            cjk += 1
        else:
            other += 1
    return max(1, cjk // 2 + other // 4)
