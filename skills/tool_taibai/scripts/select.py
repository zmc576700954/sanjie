"""
Select step of the GSSC pipeline.
Filters out noise lines from source content previews.

Supports loading custom patterns from a YAML or JSON config file.
"""

import json
import os
import re


# Built-in noise patterns (regex strings)
# Patterns that match the entire line cause the line to be dropped.
# Patterns with a capture group remove only the matched prefix, preserving the rest.
DEFAULT_NOISE_PATTERNS = [
    # ── English filler ────────────────────────────────────────────────────────
    r"(?i)^\s*let me\s+.*",
    r"(?i)^\s*i think\s+.*",
    r"(?i)^\s*based on my analysis[,;:\-]*\s*(.*)",
    r"(?i)^\s*i will\s+(.*)",               # capture group preserves actionable detail
    r"(?i)^\s*please note[,;:\-]*\s*(.*)",
    r"(?i)^\s*here is\s+(.*)",              # capture everything after "here is"
    r"(?i)^\s*as you can see[,;:\-]*\s*(.*)",
    r"(?i)^\s*of course[,;:\-]*\s*(.*)",
    r"(?i)^\s*actually[,;:\-]*\s*(.*)",
    # ── Chinese filler ────────────────────────────────────────────────────────
    r"^\s*让我来?\s*.*",
    r"^\s*我认为\s*.*",
    r"^\s*根据我的分析[，,：:\-]*\s*(.*)",
    r"^\s*我会\s*.*",
    r"^\s*请注意[，,：:\-]*\s*(.*)",
    r"^\s*以下是\s*.*",
    r"^\s*由此可见[，,：:\-]*\s*(.*)",
    r"^\s*当然[，,：:\-]*\s*(.*)",
    r"^\s*实际上[，,：:\-]*\s*(.*)",
    # ── Structural noise ──────────────────────────────────────────────────────
    r"^\s*$",
    r"^\s*={3,}\s*$",
    r"^\s*-{3,}\s*$",
]


def load_patterns_from_file(config_path: str) -> list[str]:
    """Load noise patterns from a JSON or YAML config file.

    Expected format (JSON example):
    {
        "patterns": [
            {"regex": "^\\s*filler.*", "lang": "en"},
            {"regex": "^\\s*填充.*", "lang": "zh"}
        ]
    }

    A flat list of strings is also accepted:
    ["^\\s*filler.*", "^\\s*填充.*"]

    Returns a list of regex pattern strings, or an empty list on error.
    """
    if not os.path.exists(config_path):
        return []

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try JSON first
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try YAML if pyyaml is available
            try:
                import yaml
                data = yaml.safe_load(content)
            except ImportError:
                return []
            except Exception:
                return []

        if isinstance(data, list):
            # Flat list of pattern strings
            return [p for p in data if isinstance(p, str)]

        if isinstance(data, dict) and "patterns" in data:
            patterns = []
            for entry in data["patterns"]:
                if isinstance(entry, str):
                    patterns.append(entry)
                elif isinstance(entry, dict) and "regex" in entry:
                    patterns.append(entry["regex"])
            return patterns

        return []
    except Exception:
        return []


def select_content(
    raw_sources: dict,
    noise_patterns: list[str] = None,
    keep_sections: list[str] = None,
    config_path: str = None,
) -> dict:
    """
    Filter out noise lines from each source's content_preview.

    Args:
        raw_sources: Output from gather_sources, a dict with a 'sources' list.
        noise_patterns: Optional list of regex patterns to override/extend defaults.
        keep_sections: Optional list of section names to preserve (reserved for future use).
        config_path: Optional path to a JSON/YAML config file with custom patterns.
                     If provided AND noise_patterns is None, patterns are loaded from file.

    Returns:
        A dict with filtered_sources and removed_stats.
    """
    if noise_patterns is not None:
        patterns = noise_patterns
    elif config_path:
        file_patterns = load_patterns_from_file(config_path)
        patterns = file_patterns if file_patterns else DEFAULT_NOISE_PATTERNS
    else:
        patterns = DEFAULT_NOISE_PATTERNS

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
                    if m.lastindex is not None:
                        preserved_tail = m.group(1)
                    break

            if is_noise:
                noise_count += 1
                stripped = line.strip()
                if stripped == "" or stripped.startswith("=") or stripped.startswith("-"):
                    filler_count += 1
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
