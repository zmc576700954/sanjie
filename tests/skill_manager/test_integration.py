from pathlib import Path

import pytest
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from skill_manager.builtin_skills import load_builtin_skills
from skill_manager.server import create_server
from skill_manager.store import FileSystemStore


@pytest.mark.anyio
async def test_resolve_code_review_python(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    load_builtin_skills(store)
    server = create_server(store)

    # Use internal handler directly for testing
    list_tools_handler = server.request_handlers[ListToolsRequest]
    result = await list_tools_handler(None)
    tools = {t.name: t for t in result.root.tools}
    assert "resolve_skill" in tools

    call_tool_handler = server.request_handlers[CallToolRequest]
    req = CallToolRequest(
        params=CallToolRequestParams(
            name="resolve_skill",
            arguments={
                "name": "code_review",
                "language": "python",
                "action": "self_review",
                "trigger": "/review",
            },
        )
    )
    result = await call_tool_handler(req)
    text = result.root.content[0].text
    assert "Code Review" in text
    assert "Python-Specific Guidance" in text
    assert "Self-Review Mode" in text
