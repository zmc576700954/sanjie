"""Tests for SQLite FTS5 keyword index."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.indexer.sqlite_idx import SQLiteFTS5Index
from agents_dev.docs.models import DocChunk, SearchFilters


@pytest.fixture
def idx(tmp_path):
    return SQLiteFTS5Index(tmp_path / "index.db")


def _chunk(doc_id: str, content: str, contributor=None) -> DocChunk:
    return DocChunk(
        chunk_id=f"{doc_id}_1",
        doc_id=doc_id,
        doc_title="Title",
        doc_type="how-to",
        author="alice",
        contributor=contributor,
        session_id="s1",
        tags=["api"],
        heading_path=["Title"],
        content=content,
        source_path=Path(f"{doc_id}.md"),
    )


def test_index_and_search(idx):
    idx.index_chunks([_chunk("d1", "deploy to production")])
    results = idx.search("deploy", SearchFilters())
    assert len(results) == 1
    assert results[0].doc_id == "d1"


def test_search_filters_by_author(idx):
    idx.index_chunks([
        _chunk("d1", "deploy", contributor=None),
        _chunk("d2", "deploy", contributor="bob"),
    ])
    results = idx.search("deploy", SearchFilters(contributor="bob"))
    assert len(results) == 1
    assert results[0].doc_id == "d2"


def test_clear_index(idx):
    idx.index_chunks([_chunk("d1", "deploy")])
    idx.clear()
    results = idx.search("deploy", SearchFilters())
    assert results == []
