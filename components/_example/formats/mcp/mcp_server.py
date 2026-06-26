#!/usr/bin/env python3
"""MCP Server: example_skill - Example skill that demonstrates the component architecture"""

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("example_skill")

# No tool definitions

# No tool handlers

async def main():
    """Run the MCP server."""
    async with server.run() as runner:
        await runner.wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
