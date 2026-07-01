"""Tests for HybridSearcher."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.indexer.hybrid import HybridSearcher
from agents_dev.docs.indexer.sqlite_idx import SQLiteFTS5Index
from agents_dev.docs.models import DocChunk, SearchFilters


@pytest.fixture
def hybrid(tmp_path):
    keyword = SQLiteFTS5Index(tmp_path / "kw.db")
    return HybridSearcher(keyword_backend=keyword)


def _chunk(doc_id: str, content: str) -> DocChunk:
    return DocChunk(
        chunk_id=f"{doc_id}_1",
        doc_id=doc_id,
        doc_title="Title",
        doc_type="how-to",
        author="alice",
        contributor=None,
        session_id="s1",
        tags=["api"],
        heading_path=["Title"],
        content=content,
        source_path=Path(f"{doc_id}.md"),
    )


def test_keyword_mode_delegates_to_backend(hybrid):
    hybrid.keyword_backend.index_chunks([_chunk("d1", "deploy production")])
    result = hybrid.search("deploy", mode="keyword", filters=SearchFilters())
    assert result.mode == "keyword"
    assert len(result.chunks) == 1
    assert result.total == 1


def test_hybrid_mode_falls_back_when_no_vector_backend(hybrid):
    hybrid.keyword_backend.index_chunks([_chunk("d1", "deploy production")])
    result = hybrid.search("deploy", mode="hybrid", filters=SearchFilters())
    assert result.mode == "hybrid"
    assert len(result.chunks) == 1


def test_invalid_mode_raises(hybrid):
    with pytest.raises(ValueError):
        hybrid.search("x", mode="invalid", filters=SearchFilters())
