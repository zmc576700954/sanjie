"""Markdown and frontmatter parsing utilities."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import frontmatter


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter and return metadata + body.

    Args:
        content: Raw Markdown content, optionally with YAML frontmatter.

    Returns:
        Tuple of (metadata dict, markdown body string).
    """
    post = frontmatter.loads(content)
    return dict(post.metadata), post.content


def dump_frontmatter(metadata: Dict[str, Any], content: str) -> str:
    """Serialize metadata and body to a Markdown string with YAML frontmatter."""
    post = frontmatter.Post(content, **metadata)
    return frontmatter.dumps(post)
