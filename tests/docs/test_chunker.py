"""Tests for MarkdownChunker."""

from datetime import datetime
from pathlib import Path

from agents_dev.docs.chunker import MarkdownChunker
from agents_dev.docs.models import MasterDocument


def test_chunker_splits_by_headings():
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("api_deploy.md"),
    )
    content = """# API Deploy

Run pytest.

## Docker

Use docker build.

## Kubernetes

Use kubectl apply.
"""
    chunker = MarkdownChunker(size=200, overlap=0)
    chunks = chunker.chunk_document(master, lambda _: content)
    assert len(chunks) >= 2
    assert chunks[0].heading_path == ["API Deploy"]
    assert any("Docker" in c.heading_path for c in chunks)
    assert all(c.doc_id == "api_deploy" for c in chunks)


def test_chunker_addendum_is_single_chunk():
    from agents_dev.docs.models import Addendum

    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("api_deploy.md"),
    )
    addendum = Addendum(
        addendum_id="api_deploy.bob",
        parent_doc_id="api_deploy",
        contributor="bob",
        summary="Docker notes",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("api_deploy.bob.md"),
    )
    chunker = MarkdownChunker(size=512, overlap=0)
    chunks = chunker.chunk_addendum(addendum, master, lambda _: "Docker deploy notes.")
    assert len(chunks) == 1
    assert chunks[0].contributor == "bob"
