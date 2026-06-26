# Cursor Format Specification

## Overview

The Cursor format generates SKILL.md files compatible with the Cursor AI code editor.
The format is similar to Claude's SKILL.md with Cursor-specific additions such as
the `cursorVersion` field in the frontmatter.

## Generated Files

### SKILL.md

Skill definition with YAML frontmatter and Cursor-specific fields.

**Structure:**

```markdown
---
name: <component_name>
description: <component_description>
version: <component_version>
cursorVersion: ">=0.40"
---

# <component_name>

<component_description>

## Instructions

<instructions>

## Tools

- **<tool_name>**: <tool_description>

## Examples

**Input:** <example_input>
**Output:** <example_output>
```

**Requirements:**
- Must start with YAML frontmatter (--- delimiters)
- Frontmatter must include `name` field
- Must have an `## Instructions` section
- `cursorVersion` field should be present in frontmatter

### cursor_config.json

Cursor configuration file.

**Structure:**

```json
{
  "skills": ["<component_name>"],
  "mcpServers": {},
  "cursorRules": {
    "include": ["<component_name>"]
  }
}
```

**Requirements:**
- Must be valid JSON
- Must include `skills` field

## Validation Rules

### Errors (must fix)
- Missing SKILL.md file
- Empty SKILL.md file
- Missing YAML frontmatter in SKILL.md
- Missing `name` field in frontmatter
- Missing `## Instructions` section
- Missing cursor_config.json
- Invalid JSON in cursor_config.json

### Warnings (should fix)
- Missing `cursorVersion` in frontmatter
- Missing `## Examples` section
- Missing `## Tools` section

## Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{{name}}` | manifest.json | Component name |
| `{{description}}` | manifest.json | Component description |
| `{{version}}` | manifest.json | Version |
| `{{instructions}}` | core skill.instructions | Skill instructions |
| `{{tools}}` | core agent.available_tools / tool.function_definitions | Tool definitions |
| `{{examples}}` | core skill.examples | Usage examples |
| `{{mcp_config}}` | manifest.json | MCP server configuration |

## Differences from Claude Format

The Cursor format is nearly identical to the Claude format with these differences:

1. **Frontmatter**: Adds `cursorVersion: ">=0.40"` field
2. **Config**: Uses `cursor_config.json` instead of `plugin_config.json`
3. **Cursor Rules**: Includes `cursorRules.include` configuration
4. **Tools Section**: Emphasizes available tools in the SKILL.md body

## Integration with Cursor

1. Place SKILL.md in the Cursor skills directory (`.cursor/skills/`)
2. Add cursor_config.json to the Cursor configuration
3. Configure MCP servers in `.cursor/mcp.json`
