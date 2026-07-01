"""Tests for PromptRenderer."""

from pathlib import Path

from agents_dev.docs.models import DocChunk
from agents_dev.docs.prompts.loader import PromptRenderer


def test_render_search_context(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "search_context.j2").write_text(
        "Query: {{ query }}\n{% for c in chunks %}{{ c.content }}\n{% endfor %}"
    )
    renderer = PromptRenderer(templates_dir)
    chunk = DocChunk(
        chunk_id="c1",
        doc_id="d1",
        doc_title="Title",
        doc_type="how-to",
        author="alice",
        contributor=None,
        session_id=None,
        tags=[],
        heading_path=[],
        content="Run pytest.",
        source_path=Path("d1.md"),
    )
    text = renderer.render("search_context", query="how to deploy", chunks=[chunk])
    assert "how to deploy" in text
    assert "Run pytest." in text
