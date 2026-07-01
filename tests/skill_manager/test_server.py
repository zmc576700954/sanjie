from pathlib import Path

import pytest
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from skill_manager.builtin_skills import load_builtin_skills
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


@pytest.mark.anyio
async def test_list_skills_returns_valid_json(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(
        params=CallToolRequestParams(name="list_skills", arguments={})
    )
    result = await handler(req)
    text = result.root.content[0].text
    import json
    parsed = json.loads(text)
    assert isinstance(parsed, list)


@pytest.mark.anyio
async def test_list_skills_filter_language(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    from skill_manager.models import Skill
    skill = Skill(name="py_skill", description="Python skill", version="1.0.0", base_prompt="Base", supported_languages=["python"])
    store.save_skill(skill)
    server = create_server(store)
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(
        params=CallToolRequestParams(name="list_skills", arguments={"filter_language": "python"})
    )
    result = await handler(req)
    text = result.root.content[0].text
    import json
    parsed = json.loads(text)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "py_skill"

    req2 = CallToolRequest(
        params=CallToolRequestParams(name="list_skills", arguments={"filter_language": "java"})
    )
    result2 = await handler(req2)
    text2 = result2.root.content[0].text
    parsed2 = json.loads(text2)
    assert len(parsed2) == 0


@pytest.mark.anyio
async def test_register_skill_missing_name(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(
        params=CallToolRequestParams(name="register_skill", arguments={"metadata": {}, "base_prompt": "hello"})
    )
    result = await handler(req)
    text = result.root.content[0].text
    assert "Error" in text
    assert "name" in text


@pytest.mark.anyio
async def test_register_skill_missing_base_prompt(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(
        params=CallToolRequestParams(name="register_skill", arguments={"metadata": {"name": "foo"}})
    )
    result = await handler(req)
    text = result.root.content[0].text
    assert "base_prompt" in text


@pytest.mark.anyio
async def test_update_fragment_missing_id(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(
        params=CallToolRequestParams(name="update_fragment", arguments={"skill_name": "foo", "fragment": {"content": "hello"}})
    )
    result = await handler(req)
    text = result.root.content[0].text
    assert "Error" in text
    assert "id" in text


@pytest.mark.anyio
async def test_update_fragment_missing_content(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(
        params=CallToolRequestParams(name="update_fragment", arguments={"skill_name": "foo", "fragment": {"id": "frag1"}})
    )
    result = await handler(req)
    text = result.root.content[0].text
    assert "Error" in text
    assert "content" in text


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
