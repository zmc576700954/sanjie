# MCP Format Specification

## Overview

The MCP (Model Context Protocol) format generates a Python MCP server and
configuration file. MCP is a universal protocol supported by all target tools,
making it the most portable format for tool components.

## Generated Files

### mcp_server.py

A Python MCP server file with tool definitions and handlers.

**Structure:**

```python
#!/usr/bin/env python3
"""MCP Server: <component_name> - <component_description>"""

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("<component_name>")

@server.tool()
async def <function_name>(**kwargs):
    """<function_description>"""
    # TODO: Implement <function_name> logic
    return {'status': 'not_implemented', 'function': '<function_name>'}

@server.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        Tool(name="<function_name>", description="<function_description>",
            inputSchema={...}),
    ]

async def main():
    """Run the MCP server."""
    async with server.run() as runner:
        await runner.wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Requirements:**
- Must be a valid Python file
- Must define an MCP server with at least one tool
- Must include `main()` entry point
- Must include tool handlers for all defined tools

### mcp_config.json

MCP server configuration for tool integration.

**Structure:**

```json
{
  "mcpServers": {
    "<component_name>": {
      "command": "python",
      "args": ["path/to/<component_name>_server.py"],
      "transport": "stdio"
    }
  }
}
```

**Requirements:**
- Must be valid JSON
- Must include `mcpServers` object with server configuration
- Must specify `transport` (stdio or sse)

## Validation Rules

### Errors (must fix)
- Missing mcp_server.py file
- Empty mcp_server.py file
- Missing Python server setup (Server import/instantiation)
- Missing tool handlers
- Missing main() entry point
- Missing mcp_config.json
- Invalid JSON in mcp_config.json

### Warnings (should fix)
- TODO comments remaining in generated code
- Missing tool definitions for skill/agent components

## Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{{name}}` | manifest.json | Component name |
| `{{description}}` | manifest.json | Component description |
| `{{tool_definitions}}` | core tool.function_definitions | MCP tool definition code |
| `{{tool_handlers}}` | core tool.function_definitions | MCP tool handler code |
| `{{mcp_transport}}` | manifest.json mcp_config | Transport type (stdio/sse) |

## Tool Definitions Generation

For ToolBase components, the generator converts `function_definitions` into
MCP tool definitions and handlers:

```python
# From function_definitions:
[{
    "name": "search_files",
    "description": "Search for files matching a pattern",
    "inputSchema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Search pattern"}
        }
    }
}]

# Generates:
@server.tool()
async def search_files(**kwargs):
    """Search for files matching a pattern"""
    # TODO: Implement search_files logic
    return {'status': 'not_implemented', 'function': 'search_files'}
```

For SkillBase and AgentBase components, the generated server will have
placeholder tool definitions since these component types do not have
MCP-compatible function definitions.

## Transport Modes

### stdio (default)

The server communicates via standard input/output. Most compatible mode.

```json
{
  "mcpServers": {
    "my_tool": {
      "command": "python",
      "args": ["path/to/my_tool_server.py"],
      "transport": "stdio"
    }
  }
}
```

### sse

The server communicates via Server-Sent Events over HTTP.

```json
{
  "mcpServers": {
    "my_tool": {
      "command": "python",
      "args": ["path/to/my_tool_server.py"],
      "transport": "sse"
    }
  }
}
```

Configure the transport in manifest.json:

```json
{
  "mcp_config": {
    "transport": "stdio",
    "tools": ["my_function"]
  }
}
```

## Integration with Target Tools

### Claude Code
Add MCP server config to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "my_tool": {
      "command": "python",
      "args": ["path/to/my_tool_server.py"]
    }
  }
}
```

### Cursor
Add MCP server config to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "my_tool": {
      "command": "python",
      "args": ["path/to/my_tool_server.py"]
    }
  }
}
```

### ZCode
Add MCP server configuration to the ZCode MCP settings.
