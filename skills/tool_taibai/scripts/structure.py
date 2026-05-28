"""Structure step of the GSSC pipeline.

Injects YAML frontmatter and Markdown templates based on doc_type.
"""

import re as _re
from datetime import datetime


TEMPLATES = {
    "spec": {
        "frontmatter": ["title", "date", "status:active", "author"],
        "sections": ["Summary", "Background", "Decision", "Implementation"],
    },
    "archive": {
        "frontmatter": ["title", "date", "status:archived", "author", "archival_reason"],
        "sections": ["Context", "Outcome", "Related Links"],
    },
    "handoff": {
        "frontmatter": ["from", "to", "date", "priority"],
        "sections": ["logic_chain", "root_cause", "recommended_skill", "action"],
    },
    "memory": {
        "frontmatter": ["title", "date", "status:active", "author"],
        "sections": ["Context", "Key Points", "Decisions"],
    },
}

# Characters that require quoting in YAML plain scalars.
# Includes ASCII YAML-special chars AND CJK punctuation that can confuse
# YAML parsers (full-width colon/comma, brackets, etc.)
_YAML_SPECIAL = _re.compile(
    r'[:{}\[\],&*?|>!%@`#\'"\n\r\t]'   # ASCII YAML specials
    r'|[\u3000-\u303F]'                  # CJK Symbols & Punctuation (、。，等)
    r'|[\uFF00-\uFFEF]'                  # Fullwidth Forms (：，；！？等)
    r'|^[-?]'                             # Leading - or ?
    r'|^\s|\s$'                           # Leading/trailing whitespace
)


def _yaml_escape(value: str) -> str:
    """Wrap a string value in double quotes if it contains YAML-special characters.

    Ensures Chinese punctuation (：，、) and other CJK characters survive
    round-trip through a YAML parser without corruption.
    """
    if not isinstance(value, str):
        value = str(value)
    if _YAML_SPECIAL.search(value):
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{escaped}"'
    return value


def _build_frontmatter(doc_type: str, author: str, metadata: dict) -> str:
    """Build YAML frontmatter block for the given doc_type.

    All values are passed through ``_yaml_escape`` so that Chinese characters
    and YAML-special punctuation are properly quoted.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    template = TEMPLATES.get(doc_type, TEMPLATES["spec"])
    lines = ["---"]

    for field in template["frontmatter"]:
        if ":" in field:
            key, default = field.split(":", 1)
            value = metadata.get(key, default)
        elif field == "date":
            key = field
            value = today
        elif field == "author":
            key = field
            value = author
        else:
            key = field
            value = metadata.get(key, "")

        lines.append(f"{key}: {_yaml_escape(value)}")

    lines.append("---")
    return "\n".join(lines) + "\n"


def _build_sections(doc_type: str, sources: list) -> str:
    """Build Markdown sections for the given doc_type."""
    template = TEMPLATES.get(doc_type, TEMPLATES["spec"])
    sections = template["sections"]
    content_parts = []

    auto_populate_sections = {"Summary", "Context", "Background"}

    source_text = "\n\n".join(
        s.get("content_preview", "") for s in sources if s.get("content_preview")
    )

    for section in sections:
        content_parts.append(f"## {section}")
        if section in auto_populate_sections and source_text:
            content_parts.append(source_text)
        else:
            content_parts.append("_To be filled._")
        content_parts.append("")

    return "\n".join(content_parts)


def structure_document(
    selected_sources: dict,
    doc_type: str = "spec",
    author: str = "taibai",
    metadata: dict = None,
) -> str:
    """Structure a document with YAML frontmatter and Markdown sections.

    Args:
        selected_sources: Output from select_content, containing filtered_sources.
        doc_type: Document type - "spec", "archive", "handoff", or "memory".
        author: Author name to inject into frontmatter.
        metadata: Optional additional metadata for frontmatter fields.

    Returns:
        Complete Markdown string with YAML frontmatter and sections.
    """
    if metadata is None:
        metadata = {}

    sources = selected_sources.get("filtered_sources", [])

    frontmatter = _build_frontmatter(doc_type, author, metadata)
    sections = _build_sections(doc_type, sources)

    return frontmatter + "\n" + sections
