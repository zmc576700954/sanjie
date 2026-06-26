"""CLI create command -- scaffolds a new component directory structure.

Usage:
    agents-dev create <type> <name> [options]

Creates a component directory under components/<name>/ with:
    - manifest.json with metadata
    - core/__init__.py and core/<name>.py with skeleton code
    - formats/ directory (empty, to be populated by generate)
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.tree import Tree

from core.shared.base import ComponentType
from core.shared.utils import ensure_dir, save_manifest, snake_case

console = Console()

# Map Click argument names to ComponentType values
COMPONENT_TYPES = {
    "agent": ComponentType.AGENT,
    "skill": ComponentType.SKILL,
    "tool": ComponentType.TOOL,
    "mcp_server": ComponentType.MCP_SERVER,
}

# Skeleton code templates for each component type
SKILL_SKELETON = '''"""{{name}} -- {{description}}."""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.skills.base import SkillBase


class {{ClassName}}(SkillBase):
    """{{description}}."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="{{name}}",
            type=ComponentType.SKILL,
            version="1.0.0",
            description="{{description}}",
            tags={{tags}},
            supported_tools={{supported_tools}},
        )
        super().__init__(metadata)

    @property
    def instructions(self) -> str:
        """Return the skill's usage instructions."""
        return "{{instructions_placeholder}}"

    def get_checklist(self) -> List[str]:
        """Return the skill's execution checklist."""
        return [
            "Step 1: Read input",
            "Step 2: Process data",
            "Step 3: Return result",
        ]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill's core logic.

        Args:
            input_data: Input dictionary for the skill.

        Returns:
            Dictionary containing the execution results.
        """
        message = input_data.get("message", "")
        return {"result": f"Processed: {{message}}"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data meets the skill's requirements.

        Args:
            input_data: The input dictionary to validate.

        Returns:
            True if the input is valid, False otherwise.
        """
        return True
'''

AGENT_SKELETON = '''"""{{name}} -- {{description}}."""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.agents.base import AgentBase


class {{ClassName}}(AgentBase):
    """{{description}}."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="{{name}}",
            type=ComponentType.AGENT,
            version="1.0.0",
            description="{{description}}",
            tags={{tags}},
            supported_tools={{supported_tools}},
        )
        super().__init__(metadata)

    @property
    def system_prompt(self) -> str:
        """Return the agent's system prompt."""
        return "You are {{name}}, an agent that {{description_lower}}."

    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        """Return the list of tools available to this agent."""
        return []

    def plan(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan execution steps for the given task.

        Args:
            task: The task description.
            context: Additional context for planning.

        Returns:
            A list of step dictionaries.
        """
        return [{"action": "process", "task": task}]

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Reflect on a step result.

        Args:
            result: The result from a completed step.

        Returns:
            A dictionary with reflection data.
        """
        return {"needs_adjustment": False, "assessment": "ok"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data contains a task.

        Args:
            input_data: The input dictionary to validate.

        Returns:
            True if 'task' is in input_data, False otherwise.
        """
        return "task" in input_data
'''

TOOL_SKELETON = '''"""{{name}} -- {{description}}."""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.tools.base import ToolBase


class {{ClassName}}(ToolBase):
    """{{description}}."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="{{name}}",
            type=ComponentType.TOOL,
            version="1.0.0",
            description="{{description}}",
            tags={{tags}},
            supported_tools={{supported_tools}},
        )
        super().__init__(metadata)

    @property
    def function_definitions(self) -> List[Dict[str, Any]]:
        """Return the tool's function definitions in MCP format."""
        return [
            {
                "name": "{{name}}_run",
                "description": "{{description}}",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input for the tool",
                        }
                    },
                },
            }
        ]

    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a named tool function.

        Args:
            function_name: The name of the function to invoke.
            arguments: The arguments to pass to the function.

        Returns:
            The function's return value.
        """
        if function_name == "{{name}}_run":
            return self._run_main(arguments)
        return None

    def _run_main(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Main tool execution logic.

        Args:
            arguments: The arguments for the main function.

        Returns:
            A dictionary with the result.
        """
        input_val = arguments.get("input", "")
        return {"result": f"Processed: {{input_val}}"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data contains a function name.

        Args:
            input_data: The input dictionary to validate.

        Returns:
            True if 'function' is in input_data, False otherwise.
        """
        return "function" in input_data
'''

MCP_SERVER_SKELETON = '''"""{{name}} -- {{description}} (MCP Server)."""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.tools.base import ToolBase
from core.mcp_base.server import MCPServerBase


class {{ClassName}}Tool(ToolBase):
    """Tool implementation for the {{name}} MCP server."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="{{name}}_tool",
            type=ComponentType.TOOL,
            version="1.0.0",
            description="{{description}}",
        )
        super().__init__(metadata)

    @property
    def function_definitions(self) -> List[Dict[str, Any]]:
        """Return the tool's function definitions in MCP format."""
        return [
            {
                "name": "{{name}}_run",
                "description": "{{description}}",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input for the tool",
                        }
                    },
                },
            }
        ]

    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a named tool function.

        Args:
            function_name: The name of the function to invoke.
            arguments: The arguments to pass to the function.

        Returns:
            The function's return value.
        """
        if function_name == "{{name}}_run":
            input_val = arguments.get("input", "")
            return {"result": f"Processed: {{input_val}}"}
        return None

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data contains a function name."""
        return "function" in input_data


class {{ClassName}}Server(MCPServerBase):
    """MCP Server for {{name}}."""

    def __init__(self) -> None:
        super().__init__(name="{{name}}", version="1.0.0")
        self.register_tool({{ClassName}}Tool())

    def get_server_info(self) -> Dict[str, Any]:
        """Return server metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "description": "{{description}}",
        }
'''

SKELETONS = {
    ComponentType.SKILL: SKILL_SKELETON,
    ComponentType.AGENT: AGENT_SKELETON,
    ComponentType.TOOL: TOOL_SKELETON,
    ComponentType.MCP_SERVER: MCP_SERVER_SKELETON,
}


def _to_class_name(name: str) -> str:
    """Convert a snake_case name to CamelCase class name.

    Args:
        name: The snake_case component name.

    Returns:
        The CamelCase class name.
    """
    return "".join(part.capitalize() for part in name.split("_"))


def _render_skeleton(
    skeleton: str,
    name: str,
    description: str,
    tags: List[str],
    supported_tools: List[str],
) -> str:
    """Render a skeleton template with the given values.

    Args:
        skeleton: The skeleton template string.
        name: The component name.
        description: The component description.
        tags: The component tags.
        supported_tools: The supported tool names.

    Returns:
        The rendered skeleton code.
    """
    class_name = _to_class_name(name)
    result = skeleton
    result = result.replace("{{ClassName}}", class_name)
    result = result.replace("{{name}}", name)
    result = result.replace("{{description}}", description)
    result = result.replace("{{description_lower}}", description.lower())
    result = result.replace("{{tags}}", repr(tags))
    result = result.replace("{{supported_tools}}", repr(supported_tools))
    result = result.replace("{{instructions_placeholder}}", description)
    return result


def _build_manifest(
    name: str,
    component_type: ComponentType,
    description: str,
    tools: List[str],
    tags: List[str],
) -> Dict[str, Any]:
    """Build a manifest.json dictionary for a new component.

    Args:
        name: The component name.
        component_type: The component type.
        description: The component description.
        tools: The supported tool names.
        tags: The component tags.

    Returns:
        A dictionary representing the manifest.json content.
    """
    today = date.today().isoformat()
    manifest: Dict[str, Any] = {
        "name": name,
        "type": component_type.value,
        "version": "1.0.0",
        "description": description,
        "author": "",
        "created": today,
        "updated": today,
        "tags": tags,
        "core_dependencies": [],
        "supported_tools": tools,
        "config_schema": {},
    }

    if component_type == ComponentType.MCP_SERVER:
        manifest["mcp_config"] = {
            "transport": "stdio",
            "tools": [f"{name}_run"],
        }

    return manifest


@click.command("create")
@click.argument("component_type", type=click.Choice(list(COMPONENT_TYPES.keys())))
@click.argument("name")
@click.option("--description", "-d", default="", help="Component description")
@click.option(
    "--tools",
    "-t",
    default="claude,zcode,cursor,reasionix,mcp",
    help="Comma-separated list of supported tools",
)
@click.option("--tags", default="", help="Comma-separated list of tags")
def create_cmd(
    component_type: str,
    name: str,
    description: str,
    tools: str,
    tags: str,
) -> None:
    """Create a new component scaffold.

    COMPONENT_TYPE is one of: agent, skill, tool, mcp_server.
    NAME is the component identifier in snake_case.

    Examples:

        agents-dev create skill data_analysis

        agents-dev create skill data_analysis --description "Data analysis skill"

        agents-dev create tool file_utils --tools claude,mcp --tags "files,utils"
    """
    # Normalize name to snake_case
    name = snake_case(name)

    # Validate name is not empty
    if not name or name.startswith("_"):
        console.print(f"[red]Error:[/red] Invalid component name '{name}'. "
                      "Name must be a non-empty snake_case identifier not starting with '_'.")
        raise SystemExit(1)

    # Determine project root (where components/ directory lives)
    project_root = Path.cwd()
    components_dir = project_root / "components"
    component_dir = components_dir / name

    # Check if component already exists
    if component_dir.exists():
        console.print(f"[red]Error:[/red] Component '{name}' already exists at {component_dir}")
        raise SystemExit(1)

    # Parse tools and tags
    tool_list = [t.strip() for t in tools.split(",") if t.strip()]
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Validate tool names
    valid_tools = {"claude", "zcode", "cursor", "reasionix", "mcp"}
    invalid_tools = set(tool_list) - valid_tools
    if invalid_tools:
        console.print(f"[red]Error:[/red] Invalid tool names: {', '.join(invalid_tools)}")
        console.print(f"Valid tools are: {', '.join(sorted(valid_tools))}")
        raise SystemExit(1)

    # Get component type enum
    ctype = COMPONENT_TYPES[component_type]

    # Use description or generate a default
    if not description:
        description = f"A {component_type} component named {name}"

    # Create directory structure
    core_dir = component_dir / "core"
    formats_dir = component_dir / "formats"
    ensure_dir(core_dir)
    ensure_dir(formats_dir)

    # Create manifest.json
    manifest = _build_manifest(name, ctype, description, tool_list, tag_list)
    manifest_path = component_dir / "manifest.json"
    save_manifest(manifest_path, manifest)

    # Create core/__init__.py
    init_content = f'"""Component {name} -- core implementation."""\n'
    (core_dir / "__init__.py").write_text(init_content, encoding="utf-8")

    # Create core/<name>.py with skeleton code
    skeleton = SKELETONS[ctype]
    rendered = _render_skeleton(skeleton, name, description, tag_list, tool_list)
    core_file = core_dir / f"{name}.py"
    core_file.write_text(rendered, encoding="utf-8")

    # Print success message with tree
    tree = Tree(f"[green]Created component:[/green] {name}")
    tree.add(f"manifest.json")
    core_branch = tree.add("core/")
    core_branch.add("__init__.py")
    core_branch.add(f"{name}.py")
    tree.add("formats/  (empty -- run 'agents-dev generate' to populate)")

    console.print(tree)
    console.print()
    console.print(f"[dim]Next steps:[/dim]")
    console.print(f"  1. Edit [bold]{core_file}[/bold] to implement your logic")
    console.print(f"  2. Run [bold]agents-dev generate {name}[/bold] to create format files")
    console.print(f"  3. Run [bold]agents-dev validate {name}[/bold] to check formats")
    console.print(f"  4. Run [bold]agents-dev export {name}[/bold] to export to target tools")
