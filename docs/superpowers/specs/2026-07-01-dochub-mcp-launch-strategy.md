# DocHub MCP Launch Strategy

**Date:** 2026-07-01  
**Type:** Implementation Plan  
**Status:** Approved

---

## 1. Goal

Provide a single, reliable way to launch the DocHub MCP server so AI clients (Claude Desktop, Cursor, ZCode) can connect to the knowledge base via stdio transport.

## 2. Current State

- `agents_dev/docs/mcp/server.py` defines `DocHubMCPServer` based on the project's own `MCPServerBase` abstraction.
- `cli/docs_cmd.py` has `agents-dev docs serve`, but it only prints a message and does not actually run an MCP transport.
- `components/dochub/formats/mcp/mcp_server.py` uses the official MCP SDK but has an incorrect `server.run()` call and duplicates logic.
- MCP config files point to `agents-dev docs serve --config ./dochub.yaml`, which is not yet functional.

## 3. Design Decisions

### 3.1 Transport

Support **stdio only** for now. It is the most compatible transport across Claude Desktop, Cursor, and ZCode.

### 3.2 Server Implementation

Use the official `mcp` Python SDK (`mcp.server.Server` + `mcp.server.stdio.stdio_server`).

Create a single shared module `agents_dev/docs/mcp/stdio_server.py` that:
- Loads `DocHubConfig`
- Instantiates `DocHubTool`
- Registers `list_tools` and `call_tool` handlers
- Runs the stdio transport

Both the CLI command and the generated `components/dochub/formats/mcp/mcp_server.py` will delegate to this module.

### 3.3 CLI Command

`agents-dev docs serve --config <dochub-dir>` will:
1. Load `dochub.yaml`
2. Call `run_dochub_stdio_server(config)`
3. Keep the process alive handling MCP messages

### 3.4 Generated Files

- `components/dochub/formats/mcp/mcp_server.py`: thin wrapper around `agents_dev.docs.mcp.stdio_server`
- `components/dochub/formats/claude/plugin_config.json`: `mcpServers.dochub.command = ["agents-dev", "docs", "serve", "--config", "<path>"]`
- `components/dochub/formats/cursor/cursor_config.json`: same as above
- `components/dochub/formats/mcp/mcp_config.json`: same as above

### 3.5 Per-Client Connection Guide

#### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dochub": {
      "command": "agents-dev",
      "args": ["docs", "serve", "--config", "/path/to/team-kb"]
    }
  }
}
```

#### Cursor

Add to Cursor Settings → MCP:

```json
{
  "mcpServers": {
    "dochub": {
      "command": "agents-dev",
      "args": ["docs", "serve", "--config", "/path/to/team-kb"]
    }
  }
}
```

#### ZCode

Use the generated `Command.md` plus the same MCP config. ZCode can invoke `agents-dev docs serve` as an MCP server.

## 4. Testing

- Unit test for `stdio_server` module: verify tool listing returns DocHub tools.
- CLI test: verify `agents-dev docs serve --help` shows correct options.
- Validate generated MCP format files with `agents-dev validate dochub`.

## 5. Rollout Steps

1. Implement `agents_dev/docs/mcp/stdio_server.py`
2. Update `agents_dev/docs/mcp/server.py` to delegate to stdio_server (or deprecate)
3. Update `cli/docs_cmd.py` serve command to actually run the server
4. Update generated `components/dochub/formats/mcp/mcp_server.py`
5. Update all MCP config JSON files
6. Add tests
7. Run full test suite
8. Commit
