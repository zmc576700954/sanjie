"""CLI generate command -- generates format files for a component.

Usage:
    agents-dev generate <name> [tools]...

If no tools are specified, generates for all supported tools listed in the
component's manifest.json. Uses ComponentExporter to produce the files.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List

import click
from rich.console import Console
from rich.table import Table

from core.shared.base import ComponentMetadata, ComponentType, CoreComponent
from core.shared.utils import load_manifest
from migration.exporter import ComponentExporter

console = Console()


def _load_component(component_dir: Path, manifest: Dict[str, Any]) -> CoreComponent:
    """Load a core component from its directory.

    Dynamically imports the component's Python module and instantiates
    the component class found within it.

    Args:
        component_dir: Path to the component directory (e.g. components/my_skill/).
        manifest: The manifest.json content.

    Returns:
        An instance of the component's core class.

    Raises:
        click.ClickException: If the component cannot be loaded.
    """
    name = manifest["name"]
    ctype_str = manifest["type"]
    core_dir = component_dir / "core"
    core_file = core_dir / f"{name}.py"

    if not core_file.exists():
        raise click.ClickException(
            f"Core implementation not found: {core_file}\n"
            f"Make sure the component has a core/{name}.py file."
        )

    # Add the project root and component core dir to sys.path temporarily
    project_root = component_dir.parent.parent
    paths_to_add = [str(project_root), str(core_dir)]
    added_paths = []
    for p in paths_to_add:
        if p not in sys.path:
            sys.path.insert(0, p)
            added_paths.append(p)

    try:
        # Import the module
        module_name = f"{name}"
        spec = importlib.util.spec_from_file_location(module_name, core_file)
        if spec is None or spec.loader is None:
            raise click.ClickException(f"Cannot load module from {core_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the component class in the module -- must be a concrete
        # (non-abstract) subclass of CoreComponent defined *in* the module file.
        component_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, CoreComponent)
                and attr is not CoreComponent
                and not getattr(attr, "__abstractmethods__", None)
                and getattr(attr, "__module__", None) == module.__name__
            ):
                component_class = attr
                break

        if component_class is None:
            raise click.ClickException(
                f"No CoreComponent subclass found in {core_file}"
            )

        # Instantiate the component
        component = component_class()
        return component

    except Exception as exc:
        if isinstance(exc, click.ClickException):
            raise
        raise click.ClickException(f"Failed to load component '{name}': {exc}")

    finally:
        # Clean up sys.path
        for p in added_paths:
            if p in sys.path:
                sys.path.remove(p)


def _resolve_tools(manifest: Dict[str, Any], requested_tools: List[str]) -> List[str]:
    """Resolve the list of target tools from manifest and CLI arguments.

    If requested_tools is empty, uses all tools from the manifest's
    supported_tools list. Otherwise, validates that requested tools are
    in the manifest's supported_tools.

    Args:
        manifest: The manifest.json content.
        requested_tools: Tool names specified on the command line (may be empty).

    Returns:
        A list of tool names to generate for.

    Raises:
        click.ClickException: If any requested tool is not supported.
    """
    supported = manifest.get("supported_tools", ["claude", "zcode", "cursor", "reasionix", "mcp"])

    if not requested_tools:
        return supported

    # Validate requested tools
    invalid = set(requested_tools) - set(supported)
    if invalid:
        raise click.ClickException(
            f"Tool(s) not supported by this component: {', '.join(invalid)}\n"
            f"Supported tools: {', '.join(supported)}"
        )

    return requested_tools


@click.command("generate")
@click.argument("name")
@click.argument("tools", nargs=-1)
def generate_cmd(name: str, tools: tuple) -> None:
    """Generate format files for a component.

    NAME is the component identifier.

    If no TOOLS are specified, generates for all supported tools in the
    component's manifest.

    Examples:

        agents-dev generate my_skill

        agents-dev generate my_skill claude mcp
    """
    # Find the component directory
    project_root = Path.cwd()
    component_dir = project_root / "components" / name

    if not component_dir.exists():
        console.print(f"[red]Error:[/red] Component '{name}' not found at {component_dir}")
        raise SystemExit(1)

    # Load manifest
    manifest_path = component_dir / "manifest.json"
    if not manifest_path.exists():
        console.print(f"[red]Error:[/red] manifest.json not found at {manifest_path}")
        raise SystemExit(1)

    manifest = load_manifest(manifest_path)

    # Resolve target tools
    tool_list = _resolve_tools(manifest, list(tools))

    # Load component
    component = _load_component(component_dir, manifest)

    # Create exporter and generate formats
    exporter = ComponentExporter.create_default()

    # Generate without writing (we'll write to the component's formats/ dir)
    results = exporter.export(component, manifest, tool_list, component_dir)

    # Display results
    table = Table(title=f"Generated Formats for '{name}'")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    has_errors = False
    for tool_name, result in results.items():
        if result.valid:
            status = "[green]OK[/green]"
        else:
            status = "[red]FAILED[/red]"
            has_errors = True

        details = []
        if result.errors:
            details.extend(f"Error: {e}" for e in result.errors)
        if result.warnings:
            details.extend(f"Warning: {w}" for w in result.warnings)
        detail_text = "; ".join(details) if details else "No issues"

        table.add_row(tool_name, status, detail_text)

    console.print(table)

    if has_errors:
        raise SystemExit(1)
    else:
        console.print()
        console.print(f"[green]Successfully generated formats for {name}[/green]")
        console.print(f"[dim]Files written to {component_dir / 'formats'}[/dim]")
