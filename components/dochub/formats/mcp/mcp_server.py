#!/usr/bin/env python3
"""DocHub MCP server entry point.

Exposes DocHub knowledge-base tools via the Model Context Protocol.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from a checkout without install
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.types import TextContent, Tool

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool


def main() -> None:
    parser = argparse.ArgumentParser(description="DocHub MCP server")
    parser.add_argument(
        "--config",
        default=".",
        help="Path to the DocHub knowledge base directory containing dochub.yaml",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if (config_path / "dochub.yaml").exists():
        yaml_path = config_path / "dochub.yaml"
    else:
        yaml_path = config_path

    config = DocHubConfig.from_yaml(yaml_path)
    dochub = DocHubTool(config)

    server = Server("dochub")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(name=fd["name"], description=fd["description"], inputSchema=fd["inputSchema"])
            for fd in dochub.function_definitions
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        result = dochub.run(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    async def main():
        async with server.run() as runner:
            await runner.wait()

    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    main()
