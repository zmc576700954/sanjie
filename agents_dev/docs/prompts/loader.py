"""Jinja2-based prompt template renderer for DocHub."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptRenderer:
    """Load and render Jinja2 prompt templates."""

    def __init__(self, templates_path: Path) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @classmethod
    def default(cls) -> "PromptRenderer":
        """Return a renderer using built-in templates."""
        base = Path(__file__).parent / "templates"
        return cls(base)

    def render(self, template_name: str, **context: Any) -> str:
        """Render a named template with the given context."""
        template = self.env.get_template(f"{template_name}.j2")
        return template.render(**context)
