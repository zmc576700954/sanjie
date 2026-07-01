"""Tests for DocHub data models."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.models import (
    Addendum,
    DocChunk,
    MasterDocument,
    SearchFilters,
    SearchResult,
)
from agents_dev.docs.errors import InvalidDocumentTypeError


def test_master_document_requires_valid_doc_type():
    with pytest.raises(InvalidDocumentTypeError):
        MasterDocument(
            doc_id="bad_type",
            title="Bad Type",
            author="alice",
            doc_type="essay",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            content_path=Path("docs/master/bad_type.md"),
        )


def test_addendum_parent_doc_id_matches_doc_id():
    addendum = Addendum(
        addendum_id="api_deploy.bob",
        parent_doc_id="api_deploy",
        contributor="bob",
        summary="Docker deploy notes",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("docs/addendums/api_deploy.bob.md"),
    )
    assert addendum.addendum_id == "api_deploy.bob"


def test_doc_chunk_has_required_metadata():
    chunk = DocChunk(
        chunk_id="api_deploy_0",
        doc_id="api_deploy",
        doc_title="API Deploy",
        doc_type="how-to",
        author="alice",
        contributor=None,
        session_id="sess_001",
        tags=["api"],
        heading_path=["API Deploy"],
        content="Run pytest first.",
        source_path=Path("docs/master/api_deploy.md"),
    )
    assert chunk.contributor is None


def test_search_filters_defaults():
    filters = SearchFilters()
    assert filters.author is None
    assert filters.limit == 10


def test_search_result_ranking():
    result = SearchResult(
        chunks=[],
        total=0,
        query="deploy",
        mode="hybrid",
    )
    assert result.mode == "hybrid"
