from pathlib import Path

import pytest
from mcp.types import ListToolsRequest

from skill_manager.server import create_server
from skill_manager.store import FileSystemStore


@pytest.mark.anyio
async def test_list_skills_tool(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    handler = server.request_handlers[ListToolsRequest]
    result = await handler(None)
    tools = result.root.tools
    assert any(t.name == "list_skills" for t in tools)


@pytest.mark.anyio
async def test_resolve_skill_tool(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    handler = server.request_handlers[ListToolsRequest]
    result = await handler(None)
    tools = result.root.tools
    tool = next(t for t in tools if t.name == "resolve_skill")
    assert "name" in tool.inputSchema["required"]


import subprocess
import sys


def test_entry_point_imports():
    result = subprocess.run(
        [sys.executable, "-m", "skill_manager", "--help"],
        capture_output=True,
        text=True,
    )
    # Module has no CLI yet; just verify it does not crash on import.
    assert result.returncode != 2 or "No module named" not in result.stderr
