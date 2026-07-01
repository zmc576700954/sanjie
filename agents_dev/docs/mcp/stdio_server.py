"""DocHub MCP server using the official MCP Python SDK (stdio transport).

This module is the single shared entry point for running DocHub as an MCP
server. It is used by:

- ``agents-dev docs serve`` CLI command
- The generated ``components/dochub/formats/mcp/mcp_server.py`` script
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool


def _make_dochub_server(config: DocHubConfig) -> Server:
    """Create and configure an MCP Server instance for DocHub."""
    dochub = DocHubTool(config)

    server = Server(
        name="dochub",
        version="1.0.0",
        instructions=(
            "DocHub team knowledge base. Use doc_search, doc_query, doc_read, "
            "doc_create, doc_update_master, doc_add_addendum, and doc_index_status "
            "to manage and query the knowledge base."
        ),
    )

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name=fd["name"], description=fd["description"], inputSchema=fd["inputSchema"])
            for fd in dochub.function_definitions
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        result = dochub.run(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    return server


async def run_dochub_stdio_server(config: DocHubConfig) -> None:
    """Run the DocHub MCP server over stdio transport."""
    server = _make_dochub_server(config)
    init_options = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


def serve_from_path(config_path: Path) -> None:
    """Load config from *config_path* and run the stdio server.

    *config_path* may be either the DocHub base directory or the dochub.yaml
    file itself.
    """
    if config_path.is_dir():
        yaml_path = config_path / "dochub.yaml"
    else:
        yaml_path = config_path

    if not yaml_path.exists():
        print(f"Error: dochub.yaml not found at {yaml_path}", file=sys.stderr)
        sys.exit(1)

    config = DocHubConfig.from_yaml(yaml_path)

    import asyncio

    asyncio.run(run_dochub_stdio_server(config))
