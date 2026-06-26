"""CLI export command -- exports a component to target tool formats.

Usage:
    agents-dev export <name> [tools]... --output <path>

Generates, validates, and writes format files for the specified tools.
Reports validation results (pass/fail per tool). Exits with code 1 if
any validation errors occur.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import click
from rich.console import Console
from rich.table import Table

from core.shared.base import CoreComponent
from core.shared.utils import load_manifest
from migration.exporter import ComponentExporter
from migration.validators.base import ValidationResult
from cli.generate_cmd import _load_component, _resolve_tools

console = Console()


@click.command("export")
@click.argument("name")
@click.argument("tools", nargs=-1)
@click.option("--output", "-o", "output_path", default=None,
              help="Output directory (default: component's own directory)")
@click.option("--all", "export_all", is_flag=True,
              help="Export to all supported tools")
def export_cmd(
    name: str,
    tools: tuple,
    output_path: str | None,
    export_all: bool,
) -> None:
    """Export a component to target tool formats.

    Generates format files, validates them, and writes them to the output
    directory. Prints validation results per tool. Exits with code 1 if
    any validation errors occur.

    NAME is the component identifier.

    If no TOOLS are specified and --all is not set, exports to all tools
    listed in the component's manifest.

    Examples:

        agents-dev export my_skill claude

        agents-dev export my_skill claude mcp --output /path/to/project

        agents-dev export my_skill --all
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
    if export_all:
        tool_list = manifest.get(
            "supported_tools",
            ["claude", "zcode", "cursor", "reasionix", "mcp"],
        )
    else:
        tool_list = _resolve_tools(manifest, list(tools))

    if not tool_list:
        console.print("[yellow]No target tools specified.[/yellow]")
        return

    # Load component
    component = _load_component(component_dir, manifest)

    # Determine output directory
    if output_path:
        output_dir = Path(output_path)
    else:
        output_dir = component_dir

    # Create exporter and run export
    exporter = ComponentExporter.create_default()
    results = exporter.export(component, manifest, tool_list, output_dir)

    # Display results
    table = Table(title=f"Export Results for '{name}'")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Errors", style="red")
    table.add_column("Warnings", style="yellow")
    table.add_column("Output", style="dim")

    has_errors = False
    for tool_name, result in results.items():
        if result.valid:
            status = "[green]PASS[/green]"
        else:
            status = "[red]FAIL[/red]"
            has_errors = True

        errors = "\n".join(result.errors) if result.errors else "-"
        warnings = "\n".join(result.warnings) if result.warnings else "-"
        tool_output = str(output_dir / "formats" / tool_name)

        table.add_row(tool_name, status, errors, warnings, tool_output)

    console.print(table)

    if has_errors:
        console.print()
        console.print("[red]Export completed with errors.[/red]")
        raise SystemExit(1)
    else:
        console.print()
        console.print(f"[green]Export completed successfully.[/green]")
        console.print(f"[dim]Files written to {output_dir / 'formats'}[/dim]")
