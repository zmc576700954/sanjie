# ZCode Format Specification

## Overview

The ZCode format generates custom command definitions for the ZCode AI development
tool. Commands are defined using Command.md files with usage instructions and examples.

## Generated Files

### Command.md

The primary command definition file.

**Structure:**

```markdown
# <component_name>

<component_description>

## Usage

```
/<component_name> [arguments]
```

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
- Must have a heading with the component name
- Must have a `## Usage` section
- Must have an `## Instructions` section
- Content must not be empty

### command_config/template.json

Command configuration with argument mapping.

**Structure:**

```json
{
  "name": "<component_name>",
  "description": "<component_description>",
  "type": "command",
  "arguments": {},
  "dependencies": []
}
```

**Requirements:**
- Must be valid JSON
- Must include `name` and `description` fields

## Validation Rules

### Errors (must fix)
- Missing Command.md file
- Empty Command.md file
- Missing heading in Command.md
- Missing `## Instructions` section in Command.md

### Warnings (should fix)
- Missing `## Examples` section
- Missing `## Checklist` section

## Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{{name}}` | manifest.json | Component name |
| `{{description}}` | manifest.json | Component description |
| `{{instructions}}` | core skill.instructions | Skill instructions |
| `{{checklist}}` | core skill.get_checklist() | Checklist items |
| `{{examples}}` | core skill.examples | Usage examples |
| `{{config_schema}}` | manifest.json | Configuration schema (mapped to arguments) |
| `{{core_dependencies}}` | manifest.json | Python dependencies |

## Config Schema to Arguments Mapping

The ZCode generator maps the manifest's `config_schema` to ZCode command arguments:

```json
// manifest.json config_schema
{
  "properties": {
    "input_text": {
      "type": "string",
      "description": "The text to process"
    }
  },
  "required": ["input_text"]
}

// Maps to command_config arguments
{
  "input_text": {
    "type": "string",
    "description": "The text to process",
    "required": true
  }
}
```

## Integration with ZCode

1. Place Command.md in the ZCode commands directory
2. Place command_config/ in the ZCode configuration directory
3. The command becomes available as `/<component_name>` in ZCode
