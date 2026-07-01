"""Tests for MarkdownChunker."""

from datetime import datetime, timezone
from pathlib import Path

from agents_dev.docs.chunker import MarkdownChunker
from agents_dev.docs.models import MasterDocument


def test_chunker_splits_by_headings():
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
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


def test_chunker_respects_size():
    master = MasterDocument(
        doc_id="long_doc",
        title="Long Doc",
        author="alice",
        doc_type="reference",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        content_path=Path("long_doc.md"),
    )
    content = "# Long Doc\n\n" + "word " * 200
    chunker = MarkdownChunker(size=100, overlap=0)
    chunks = chunker.chunk_document(master, lambda _: content)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.content) <= 100


def test_chunker_overlap_is_respected():
    master = MasterDocument(
        doc_id="overlap_doc",
        title="Overlap Doc",
        author="alice",
        doc_type="reference",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        content_path=Path("overlap_doc.md"),
    )
    content = "# Overlap Doc\n\n" + "word " * 200
    chunker = MarkdownChunker(size=100, overlap=20)
    chunks = chunker.chunk_document(master, lambda _: content)
    assert len(chunks) > 1
    for i in range(1, len(chunks)):
        prev = chunks[i - 1].content
        curr = chunks[i].content
        # Check that some overlap exists between adjacent chunks
        overlap_len = 0
        for j in range(1, min(len(prev), len(curr)) + 1):
            if prev[-j:] == curr[:j]:
                overlap_len = j
        assert overlap_len > 0 or len(prev) < 100


def test_chunker_skips_headings_in_code_blocks():
    master = MasterDocument(
        doc_id="code_doc",
        title="Code Doc",
        author="alice",
        doc_type="how-to",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        content_path=Path("code_doc.md"),
    )
    content = """# Code Doc

Some intro.

```python
# This is a comment
## This is not a heading
```

## Real Heading

After code.
"""
    chunker = MarkdownChunker(size=512, overlap=0)
    chunks = chunker.chunk_document(master, lambda _: content)
    heading_paths = [c.heading_path for c in chunks]
    # The "## This is not a heading" inside the code block should not create a section
    assert any("Real Heading" in path for path in heading_paths)
    assert not any("This is not a heading" in path for path in heading_paths)


def test_chunker_addendum_is_single_chunk():
    from agents_dev.docs.models import Addendum

    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        content_path=Path("api_deploy.md"),
    )
    addendum = Addendum(
        addendum_id="api_deploy.bob",
        parent_doc_id="api_deploy",
        contributor="bob",
        summary="Docker notes",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        content_path=Path("api_deploy.bob.md"),
    )
    chunker = MarkdownChunker(size=512, overlap=0)
    chunks = chunker.chunk_addendum(addendum, master, lambda _: "Docker deploy notes.")
    assert len(chunks) == 1
    assert chunks[0].contributor == "bob"
