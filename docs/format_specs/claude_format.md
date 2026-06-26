# Claude Format Specification

## Overview

The Claude format generates files compatible with Claude Code CLI and Claude Desktop.
Skills are defined using SKILL.md files with YAML frontmatter, and plugins are
configured via plugin_config.json.

## Generated Files

### SKILL.md

The primary skill definition file with YAML frontmatter and markdown content.

**Structure:**

```markdown
---
name: <component_name>
description: <component_description>
version: <component_version>
---

# <component_name>

<component_description>

## When to Use

<when_to_use>

## Instructions

<instructions>

## Checklist

- [ ] <checklist_item_1>
- [ ] <checklist_item_2>
- [ ] <checklist_item_3>

## Examples

**Input:** <example_input>
**Output:** <example_output>
```

**Requirements:**
- Must start with YAML frontmatter (--- delimiters)
- Frontmatter must include `name` field
- Must have an `## Instructions` section

### plugin_config.json

Plugin configuration for Claude integration.

**Structure:**

```json
{
  "name": "<component_name>",
  "version": "<component_version>",
  "description": "<component_description>",
  "type": "<component_type>",
  "skills": ["<component_name>"],
  "mcpServers": {}
}
```

**Requirements:**
- Must be valid JSON
- Must include `name`, `version`, `description`, and `type` fields

### slash_commands/template.md (Skills only)

Slash command definition for quick skill invocation.

## Validation Rules

### Errors (must fix)
- Missing SKILL.md file
- Empty SKILL.md file
- Missing YAML frontmatter in SKILL.md
- Missing `name` field in frontmatter
- Missing `## Instructions` section
- Missing plugin_config.json
- Invalid JSON in plugin_config.json
- Missing required fields in plugin_config.json

### Warnings (should fix)
- Missing `## Examples` section in SKILL.md
- Missing `## Checklist` section in SKILL.md

## Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{{name}}` | manifest.json | Component name |
| `{{description}}` | manifest.json | Component description |
| `{{version}}` | manifest.json | Version |
| `{{instructions}}` | core skill.instructions | Skill instructions |
| `{{checklist}}` | core skill.get_checklist() | Checklist items |
| `{{examples}}` | core skill.examples | Usage examples |
| `{{when_to_use}}` | manifest.json or auto-generated | When to use description |
| `{{mcp_config}}` | manifest.json | MCP server configuration |

## Integration with Claude Code

1. Place SKILL.md in `.claude/skills/` directory
2. Add plugin_config.json to `.claude/plugins/` directory
3. Configure MCP servers in `.claude/settings.json`

## Integration with Claude Desktop

1. Place SKILL.md in the Claude Desktop skills directory
2. Add plugin configuration to the Claude Desktop config
3. Configure MCP servers in the Claude Desktop settings
