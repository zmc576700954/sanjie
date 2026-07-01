"""Tests for DocHub MCP tools."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.server import DocHubMCPServer
from agents_dev.docs.mcp.tools import DocHubTool
from agents_dev.docs.models import MasterDocument


@pytest.fixture
def tool(tmp_path):
    config = DocHubConfig({"name": "test-kb"}, base_path=tmp_path)
    return DocHubTool(config)


def test_doc_create_and_read(tool, tmp_path):
    result = tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest.",
        "author": "alice",
        "doc_type": "how-to",
        "tags": ["api"],
    })
    assert result["doc_id"] == "api_deploy"

    read_result = tool.run("doc_read", {"doc_id": "api_deploy"})
    assert "Run pytest." in read_result["content"]


def test_doc_search(tool):
    tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest before deploy.",
        "author": "alice",
        "doc_type": "how-to",
    })
    result = tool.run("doc_search", {"query": "pytest", "mode": "keyword"})
    assert result["total"] >= 1


def test_doc_addendum(tool):
    tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest.",
        "author": "alice",
        "doc_type": "how-to",
    })
    tool.run("doc_add_addendum", {
        "parent_doc_id": "api_deploy",
        "contributor": "bob",
        "content": "Use Docker.",
        "summary": "Docker notes",
    })
    master = tool.run("doc_read", {"doc_id": "api_deploy"})
    assert "bob" in master["addendums"]
