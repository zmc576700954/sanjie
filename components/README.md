# Component Library

This directory contains all components developed in the agents_develop environment.

## Directory Structure

Each component follows this structure:

```
component_name/
├── core/              # Tool-agnostic implementation
│   ├── __init__.py
│   └── <component>.py
├── formats/           # Generated tool-specific formats
│   ├── claude/        # Claude Code/Desktop format
│   ├── zcode/         # ZCode format
│   ├── cursor/        # Cursor format
│   ├── reasionix/     # Reasionix format
│   └── mcp/           # MCP format
└── manifest.json      # Component metadata
```

## Creating a New Component

Use the CLI to scaffold a new component:

```bash
agents-dev create skill my_skill --description "My custom skill"
```

This creates the directory structure with skeleton code. Edit the core
implementation, then generate and export formats:

```bash
agents-dev generate my_skill
agents-dev validate my_skill
agents-dev export my_skill claude --output /path/to/claude/project
```

## Example Component

The `_example/` directory contains a working example skill that demonstrates
the full component architecture. Use it as a reference when creating new
components.

## Component Types

- **skill**: Reusable skill module with instructions and checklist
- **agent**: Intelligent agent with system prompt and tool access
- **tool**: Python tool with function definitions (MCP-compatible)
- **mcp_server**: MCP server wrapping one or more tools

## Manifest Schema

Each component's `manifest.json` must include:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Component identifier (snake_case) |
| type | string | Yes | Component type (agent/skill/tool/mcp_server) |
| version | string | Yes | Semantic version |
| description | string | Yes | One-line description |
| author | string | No | Author name |
| created | string | No | Creation date (YYYY-MM-DD) |
| updated | string | No | Last update date (YYYY-MM-DD) |
| tags | array | No | Searchable tags |
| core_dependencies | array | No | Python package dependencies |
| supported_tools | array | No | Target tools (claude/zcode/cursor/reasionix/mcp) |
| config_schema | object | No | JSON Schema for configuration |
| mcp_config | object | No | MCP server configuration |
