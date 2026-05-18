"""
Select step of the GSSC pipeline.
Filters out noise lines from source content previews.
"""

import re


# Built-in noise patterns (regex strings)
# Patterns that match the entire line cause the line to be dropped.
# Patterns with a capture group remove only the matched prefix, preserving the rest.
DEFAULT_NOISE_PATTERNS = [
    r"(?i)^\s*let me\s+.*",
    r"(?i)^\s*i think\s+.*",
    r"(?i)^\s*based on my analysis[,;:\-]*\s*(.*)",
    r"(?i)^\s*i will\s+.*",
    r"(?i)^\s*please note[,;:\-]*\s*(.*)",
    r"(?i)^\s*here is\s+.*",
    r"(?i)^\s*as you can see[,;:\-]*\s*(.*)",
    r"(?i)^\s*of course[,;:\-]*\s*(.*)",
    r"(?i)^\s*actually[,;:\-]*\s*(.*)",
    r"^\s*$",
    r"^\s*={3,}\s*$",
    r"^\s*-{3,}\s*$",
]


def select_content(
    raw_sources: dict,
    noise_patterns: list[str] = None,
    keep_sections: list[str] = None,
) -> dict:
    """
    Filter out noise lines from each source's content_preview.

    Args:
        raw_sources: Output from gather_sources, a dict with a 'sources' list.
        noise_patterns: Optional list of regex patterns to override/extend defaults.
        keep_sections: Optional list of section names to preserve (reserved for future use).

    Returns:
        A dict with filtered_sources and removed_stats.
    """
    patterns = noise_patterns if noise_patterns is not None else DEFAULT_NOISE_PATTERNS
    compiled_patterns = [re.compile(p) for p in patterns]

    filtered_sources = []
    total_noise_lines = 0
    total_filler_lines = 0

    for source in raw_sources.get("sources", []):
        content_preview = source.get("content_preview", "")
        lines = content_preview.split("\n")
        kept_lines = []
        noise_count = 0
        filler_count = 0

        for line in lines:
            is_noise = False
            preserved_tail = None
            for compiled in compiled_patterns:
                m = compiled.match(line)
                if m:
                    is_noise = True
                    # If the pattern has a capture group, preserve the captured tail
                    if m.lastindex is not None:
                        preserved_tail = m.group(1)
                    break

            if is_noise:
                noise_count += 1
                # Count empty lines and decorative separators as filler
                stripped = line.strip()
                if stripped == "" or stripped.startswith("=") or stripped.startswith("-"):
                    filler_count += 1
                # If there is meaningful remaining content, keep it
                if preserved_tail is not None and preserved_tail.strip():
                    kept_lines.append(preserved_tail)
            else:
                kept_lines.append(line)

        total_noise_lines += noise_count
        total_filler_lines += filler_count

        filtered_source = {
            "path": source.get("path", ""),
            "type": source.get("type", "file"),
            "size_bytes": source.get("size_bytes", 0),
            "content_preview": "\n".join(kept_lines),
        }
        filtered_sources.append(filtered_source)

    return {
        "filtered_sources": filtered_sources,
        "removed_stats": {
            "noise_lines": total_noise_lines,
            "filler_lines": total_filler_lines,
        },
    }
