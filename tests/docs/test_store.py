"""Tests for DocumentStore."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.models import MasterDocument
from agents_dev.docs.store import DocumentStore


@pytest.fixture
def tmp_store(tmp_path):
    store = DocumentStore(tmp_path / "docs")
    return store


def test_create_and_get_master(tmp_store):
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        tags=["api"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=tmp_store.docs_path / "master" / "api_deploy.md",
    )
    created = tmp_store.create_master(master, "Run pytest.")
    assert created.doc_id == "api_deploy"

    fetched = tmp_store.get_master("api_deploy")
    assert fetched.title == "API Deploy"
    assert tmp_store.read_content(fetched.content_path) == "Run pytest."


def test_update_master_appends_delta(tmp_store):
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=tmp_store.docs_path / "master" / "api_deploy.md",
    )
    tmp_store.create_master(master, "Run pytest.")
    updated = tmp_store.update_master("api_deploy", "Then deploy.", "add deploy step")
    assert "Run pytest." in tmp_store.read_content(updated.content_path)
    assert "Then deploy." in tmp_store.read_content(updated.content_path)


def test_create_addendum(tmp_store):
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=tmp_store.docs_path / "master" / "api_deploy.md",
    )
    tmp_store.create_master(master, "Run pytest.")
    addendum = tmp_store.create_or_update_addendum(
        "api_deploy", "bob", "Docker deploy notes.", "Docker notes"
    )
    assert addendum.contributor == "bob"
    assert "Docker deploy notes" in tmp_store.read_content(addendum.content_path)

    master_after = tmp_store.get_master("api_deploy")
    assert "bob" in master_after.addendums
