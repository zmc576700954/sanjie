# Migration Guide

This guide explains how to create a component, generate format files, and
export them to target AI development tools.

## Quick Start

### 1. Create a Component

```bash
agents-dev create skill my_skill --description "My custom skill"
```

This creates the directory structure:

```
components/my_skill/
├── core/
│   ├── __init__.py
│   └── my_skill.py      # Skeleton code inheriting from SkillBase
├── formats/              # Empty -- will be populated by generate
└── manifest.json         # Component metadata
```

### 2. Implement Core Logic

Edit `components/my_skill/core/my_skill.py` to implement your skill:

```python
class MySkill(SkillBase):
    @property
    def instructions(self) -> str:
        return "Your skill instructions here."

    def get_checklist(self) -> list[str]:
        return ["Step 1: ...", "Step 2: ...", "Step 3: ..."]

    def execute(self, input_data: dict) -> dict:
        # Your core logic here
        return {"result": "done"}

    def validate_input(self, input_data: dict) -> bool:
        return "required_key" in input_data
```

### 3. Generate Format Files

```bash
# Generate for all supported tools
agents-dev generate my_skill

# Generate for specific tools only
agents-dev generate my_skill claude mcp
```

### 4. Validate Generated Formats

```bash
# Validate all formats
agents-dev validate my_skill

# Validate specific tools
agents-dev validate my_skill claude zcode
```

### 5. Export to Target Tools

```bash
# Export to a specific tool
agents-dev export my_skill claude --output /path/to/claude/project

# Export to all supported tools
agents-dev export my_skill --all

# Export multiple tools
agents-dev export my_skill claude zcode mcp
```

## Creating Different Component Types

### Skill

A skill is a reusable module with instructions and a checklist.

```bash
agents-dev create skill data_analysis \
  --description "Data analysis skill" \
  --tools claude,zcode,mcp \
  --tags "data,analysis"
```

Skills implement:
- `instructions`: Usage instructions (becomes SKILL.md / Command.md content)
- `get_checklist()`: Execution checklist
- `execute()`: Core logic
- `validate_input()`: Input validation

### Agent

An agent has a system prompt, can use tools, and follows a plan-reflect loop.

```bash
agents-dev create agent code_reviewer \
  --description "Code review agent" \
  --tools claude,mcp
```

Agents implement:
- `system_prompt`: Role definition
- `available_tools`: Tool definitions
- `plan()`: Break tasks into steps
- `reflect()`: Evaluate step results

### Tool

A tool exposes callable functions with MCP-compatible schemas.

```bash
agents-dev create tool file_searcher \
  --description "File search tool" \
  --tools mcp
```

Tools implement:
- `function_definitions`: MCP-style function definitions
- `run()`: Execute a named function
- `validate_input()`: Input validation

### MCP Server

An MCP server wraps one or more tools for the Model Context Protocol.

```bash
agents-dev create mcp_server search_server \
  --description "Search MCP server"
```

## Tool-Specific Notes

### Claude Code/Desktop

- Generates `SKILL.md` with YAML frontmatter
- Generates `plugin_config.json` for plugin configuration
- Generates slash command definitions for skills
- Supports MCP server integration

### ZCode

- Generates `Command.md` for custom commands
- Generates `command_config/template.json` with argument mapping
- Maps config_schema properties to command arguments

### Cursor

- Generates `SKILL.md` with Cursor-specific frontmatter
- Generates `cursor_config.json` for Cursor configuration
- Nearly identical to Claude format with added cursorVersion

### MCP (Universal)

- Generates `mcp_server.py` with tool definitions and handlers
- Generates `mcp_config.json` for MCP server configuration
- Uses stdio transport by default
- Supported by all tools via MCP protocol

## Manifest.json Fields

| Field | Required | Description |
|-------|----------|-------------|
| name | Yes | Component identifier (snake_case) |
| type | Yes | Component type (agent/skill/tool/mcp_server) |
| version | Yes | Semantic version |
| description | Yes | One-line description |
| author | No | Author name |
| created | No | Creation date (YYYY-MM-DD) |
| updated | No | Last update date (YYYY-MM-DD) |
| tags | No | Searchable tags |
| core_dependencies | No | Python package dependencies |
| supported_tools | No | Target tools (default: all) |
| config_schema | No | JSON Schema for configuration |
| mcp_config | No | MCP server configuration |

## Error Handling

The export pipeline handles errors gracefully:

- If a generator does not exist for a tool, it records an UnsupportedToolError
- If generation fails, it records the error and continues with other tools
- If file writing fails, it aborts that tool and records the IOError
- If validation fails, it records errors and warnings
- Exit code is 0 only if all tools pass validation
