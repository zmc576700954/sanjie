"""Tests for DocHub stdio MCP server."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.stdio_server import _make_dochub_server


@pytest.mark.asyncio
async def test_stdio_server_lists_dochub_tools(tmp_path):
    config = DocHubConfig({"name": "test-kb"}, base_path=tmp_path)
    server = _make_dochub_server(config)

    from mcp.types import ListToolsRequest

    handler = server.request_handlers[ListToolsRequest]
    response = await handler(ListToolsRequest(method="tools/list"))

    tool_names = {tool.name for tool in response.root.tools}
    assert "doc_search" in tool_names
    assert "doc_query" in tool_names
    assert "doc_read" in tool_names
    assert "doc_create" in tool_names
    assert "doc_add_addendum" in tool_names


def test_serve_from_path_exits_on_missing_config(monkeypatch, tmp_path):
    from agents_dev.docs.mcp.stdio_server import serve_from_path

    missing = tmp_path / "nonexistent" / "dochub.yaml"

    def mock_exit(code: int) -> None:
        raise SystemExit(code)

    monkeypatch.setattr("sys.exit", mock_exit)

    with pytest.raises(SystemExit):
        serve_from_path(missing)
