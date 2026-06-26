"""CLI validate command -- validates generated format files for a component.

Usage:
    agents-dev validate <name> [tools]...

Validates existing generated formats against tool specifications. Prints
validation results with errors and warnings. Exits with code 1 if any
errors are found.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import click
from rich.console import Console
from rich.table import Table

from core.shared.utils import load_manifest
from migration.exporter import ComponentExporter
from migration.validators.base import ValidationResult
from cli.generate_cmd import _load_component, _resolve_tools

console = Console()


def _read_generated_formats(component_dir: Path, tool_name: str) -> Dict[str, str]:
    """Read generated format files from a component's formats directory.

    Args:
        component_dir: Path to the component directory.
        tool_name: The tool name (e.g. "claude", "zcode").

    Returns:
        A dictionary mapping relative file paths to file contents.
    """
    formats_dir = component_dir / "formats" / tool_name
    if not formats_dir.exists():
        return {}

    generated: Dict[str, str] = {}
    for file_path in formats_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(formats_dir).as_posix()
            try:
                generated[rel_path] = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                pass

    return generated


@click.command("validate")
@click.argument("name")
@click.argument("tools", nargs=-1)
def validate_cmd(name: str, tools: tuple) -> None:
    """Validate generated format files for a component.

    NAME is the component identifier.

    If no TOOLS are specified, validates all supported tools from the
    component's manifest.

    Examples:

        agents-dev validate my_skill

        agents-dev validate my_skill claude mcp
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

    if not tool_list:
        console.print("[yellow]No tools to validate.[/yellow]")
        return

    # Create exporter to get validators
    exporter = ComponentExporter.create_default()

    # Validate each tool's generated formats
    table = Table(title=f"Validation Results for '{name}'")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Errors", style="red")
    table.add_column("Warnings", style="yellow")

    has_errors = False
    for tool_name in tool_list:
        # Read generated files from disk
        generated = _read_generated_formats(component_dir, tool_name)

        if not generated:
            table.add_row(
                tool_name,
                "[yellow]NO FILES[/yellow]",
                "No generated files found. Run 'agents-dev generate' first.",
                "-",
            )
            has_errors = True
            continue

        # Validate using the appropriate validator
        if tool_name in exporter.validators:
            result = exporter.validators[tool_name].validate(generated, manifest)
        else:
            # No validator available -- assume valid with a warning
            result = ValidationResult(
                valid=True,
                warnings=[f"No validator available for tool '{tool_name}'"],
            )

        if result.valid:
            status = "[green]PASS[/green]"
        else:
            status = "[red]FAIL[/red]"
            has_errors = True

        errors = "\n".join(result.errors) if result.errors else "-"
        warnings = "\n".join(result.warnings) if result.warnings else "-"

        table.add_row(tool_name, status, errors, warnings)

    console.print(table)

    if has_errors:
        console.print()
        console.print("[red]Validation completed with errors.[/red]")
        raise SystemExit(1)
    else:
        console.print()
        console.print("[green]All validations passed.[/green]")
