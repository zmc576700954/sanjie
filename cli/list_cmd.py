"""CLI list command -- lists all components in the components/ directory.

Usage:
    agents-dev list [type]

Lists all components with name, type, version, and supported tools.
Uses Rich for formatted table output. Optionally filter by component type.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from core.shared.base import ComponentType
from core.shared.utils import load_manifest

console = Console()

COMPONENT_TYPES = {
    "agent": ComponentType.AGENT,
    "skill": ComponentType.SKILL,
    "tool": ComponentType.TOOL,
    "mcp_server": ComponentType.MCP_SERVER,
}


def _find_components(components_dir: Path) -> list[dict]:
    """Scan the components directory for valid components.

    A valid component has a manifest.json file in its root directory.

    Args:
        components_dir: Path to the components/ directory.

    Returns:
        A list of manifest dictionaries, one per component found.
    """
    components: list[dict] = []

    if not components_dir.exists():
        return components

    for item in sorted(components_dir.iterdir()):
        if not item.is_dir():
            continue

        # Skip directories starting with __ (like __pycache__)
        if item.name.startswith("__"):
            continue

        manifest_path = item / "manifest.json"
        if not manifest_path.exists():
            continue

        try:
            manifest = load_manifest(manifest_path)
            manifest["_dir"] = str(item)
            components.append(manifest)
        except Exception:
            # Skip components with invalid manifests
            console.print(f"[yellow]Warning:[/yellow] Invalid manifest in {item}, skipping")

    return components


@click.command("list")
@click.argument("component_type", required=False, type=click.Choice(list(COMPONENT_TYPES.keys())))
def list_cmd(component_type: Optional[str]) -> None:
    """List all components, optionally filtered by type.

    COMPONENT_TYPE is one of: agent, skill, tool, mcp_server.

    Examples:

        agents-dev list

        agents-dev list skill

        agents-dev list agent
    """
    project_root = Path.cwd()
    components_dir = project_root / "components"

    # Find all components
    all_components = _find_components(components_dir)

    # Filter by type if specified
    if component_type:
        type_value = COMPONENT_TYPES[component_type].value
        filtered = [c for c in all_components if c.get("type") == type_value]
    else:
        filtered = all_components

    # Check if any components found
    if not filtered:
        if component_type:
            console.print(f"No {component_type} components found.")
        else:
            console.print("No components found.")
        console.print(f"[dim]Components directory: {components_dir}[/dim]")
        return

    # Build and display table
    table = Table(title="Components")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white", max_width=40)
    table.add_column("Supported Tools", style="dim")

    for manifest in filtered:
        name = manifest.get("name", "unknown")
        ctype = manifest.get("type", "unknown")
        version = manifest.get("version", "?")
        description = manifest.get("description", "")
        supported_tools = ", ".join(manifest.get("supported_tools", []))

        table.add_row(name, ctype, version, description, supported_tools)

    console.print(table)
    console.print()
    console.print(f"[dim]Total: {len(filtered)} component(s)[/dim]")
