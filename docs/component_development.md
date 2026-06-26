# Component Development Guide

This guide explains how to develop components for the agents_develop environment.

## Overview

Components are the building blocks of the agents_develop ecosystem. Each component
consists of:

1. **Core implementation**: Tool-agnostic Python code inheriting from a base class
2. **Manifest**: Metadata describing the component (manifest.json)
3. **Format files**: Auto-generated tool-specific adaptations (in formats/ directory)

## Creating a New Skill

Skills are reusable modules with instructions, a checklist, and examples.

### Step 1: Create the Scaffold

```bash
agents-dev create skill my_skill --description "My custom skill"
```

### Step 2: Implement the Core Logic

Edit `components/my_skill/core/my_skill.py`:

```python
from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.skills.base import SkillBase


class MySkill(SkillBase):
    """My custom skill."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="my_skill",
            type=ComponentType.SKILL,
            version="1.0.0",
            description="My custom skill",
            tags=["custom"],
            supported_tools=["claude", "zcode", "mcp"],
        )
        super().__init__(metadata)

    @property
    def instructions(self) -> str:
        """Return the skill's usage instructions.

        This text will be rendered into SKILL.md and Command.md files.
        Write clear, actionable instructions for when and how to use this skill.
        """
        return "Use this skill when you need to ..."

    def get_checklist(self) -> List[str]:
        """Return the skill's execution checklist.

        Each item becomes a checkbox in the generated SKILL.md file.
        """
        return [
            "Step 1: Read and validate input",
            "Step 2: Process the data",
            "Step 3: Return formatted result",
        ]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill's core logic.

        This is the main entry point for programmatic execution.
        """
        # Your implementation here
        return {"result": "processed"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data meets requirements."""
        # Customize validation as needed
        return True
```

### Step 3: Update the Manifest

Edit `components/my_skill/manifest.json` to add any additional metadata:

```json
{
  "name": "my_skill",
  "type": "skill",
  "version": "1.0.0",
  "description": "My custom skill",
  "tags": ["custom"],
  "supported_tools": ["claude", "zcode", "mcp"],
  "config_schema": {
    "type": "object",
    "properties": {
      "input_text": {
        "type": "string",
        "description": "The text to process"
      }
    },
    "required": ["input_text"]
  }
}
```

### Step 4: Generate and Validate

```bash
agents-dev generate my_skill
agents-dev validate my_skill
```

## Creating a New Agent

Agents have a system prompt, can use tools, and follow a plan-reflect execution loop.

### Key Methods to Implement

```python
class MyAgent(AgentBase):
    @property
    def system_prompt(self) -> str:
        """Define the agent's role and behavior."""
        return "You are an expert in ..."

    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        """Define the tools this agent can use."""
        return [
            {
                "name": "search",
                "description": "Search for information",
                "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
            }
        ]

    def plan(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break a task into execution steps."""
        return [{"action": "analyze", "task": task}]

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a step result and decide if adjustment is needed."""
        return {"needs_adjustment": False, "assessment": "ok"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "task" in input_data
```

### Agent Execution Flow

1. `execute()` receives `{"task": "...", "context": {...}}`
2. `plan()` breaks the task into steps
3. Each step is executed via `_execute_step()`
4. `reflect()` evaluates each step result
5. If adjustment is needed, re-plan
6. Returns `{"steps": [...], "results": [...]}`

## Creating a New Tool

Tools expose callable functions with MCP-compatible schemas.

### Key Methods to Implement

```python
class MyTool(ToolBase):
    @property
    def function_definitions(self) -> List[Dict[str, Any]]:
        """Define the tool's functions in MCP format."""
        return [
            {
                "name": "my_function",
                "description": "What this function does",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "First parameter"}
                    },
                    "required": ["param1"]
                }
            }
        ]

    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a named function with given arguments."""
        if function_name == "my_function":
            return self._do_something(arguments)
        return None

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "function" in input_data
```

## Implementing Core Logic

### Best Practices

1. **Keep it tool-agnostic**: Never reference specific tool formats in core code
2. **Use type hints**: All methods should have complete type annotations
3. **Write docstrings**: Every public method needs a docstring
4. **Validate early**: Check inputs at the start of execute()
5. **Return structured data**: Always return a dictionary from execute()
6. **Handle errors gracefully**: Raise appropriate exceptions from core.shared.errors

### Input Validation

Use `config_schema` in the manifest to define required fields:

```json
{
  "config_schema": {
    "type": "object",
    "properties": {
      "input_text": {"type": "string", "description": "Required text input"}
    },
    "required": ["input_text"]
  }
}
```

Then `validate_input()` will automatically check for required keys if you
use the default SkillBase implementation.

### Configuration

Use `configure()` to set runtime settings:

```python
component.configure({"verbose": True, "max_results": 100})
```

Access configuration in your methods:

```python
def execute(self, input_data):
    verbose = self._config.get("verbose", False)
    max_results = self._config.get("max_results", 10)
    # ...
```

## Testing Components

### Unit Tests

Create unit tests for your component's core logic:

```python
# tests/test_my_skill.py
from core.shared.base import ComponentMetadata, ComponentType


def test_my_skill_execute():
    from components.my_skill.core.my_skill import MySkill

    skill = MySkill()
    result = skill.execute({"message": "hello"})
    assert "result" in result
    assert skill.validate_input({"message": "hello"})
```

### Integration Tests

Test the full workflow:

```python
def test_my_skill_workflow():
    # Generate
    exporter = ComponentExporter.create_default()
    manifest = load_manifest(Path("components/my_skill/manifest.json"))
    component = MySkill()
    results = exporter.export(component, manifest, ["claude"], output_dir)

    # Verify
    assert results["claude"].valid
```

## Component Directory Layout

```
components/my_skill/
├── core/
│   ├── __init__.py          # Package init
│   └── my_skill.py          # Core implementation
├── formats/                  # Generated (do not edit directly)
│   ├── claude/
│   │   ├── SKILL.md
│   │   └── plugin_config.json
│   ├── zcode/
│   │   └── Command.md
│   └── mcp/
│       ├── mcp_server.py
│       └── mcp_config.json
└── manifest.json             # Component metadata
```

Note: Files in `formats/` are auto-generated. If you need tool-specific
customizations, edit the format templates in `formats/<tool>/` at the
project level, not the generated files.
