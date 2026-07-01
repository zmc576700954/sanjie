"""CLI main entry point for agents-dev.

Provides the top-level Click group and registers all subcommands.
"""

from __future__ import annotations

import click

from cli.create_cmd import create_cmd
from cli.docs_cmd import docs_cmd
from cli.export_cmd import export_cmd
from cli.generate_cmd import generate_cmd
from cli.list_cmd import list_cmd
from cli.validate_cmd import validate_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="agents-dev")
def main() -> None:
    """agents-dev -- Multi-tool agent/skill development environment."""


# Register all subcommands
main.add_command(create_cmd)
main.add_command(generate_cmd)
main.add_command(export_cmd)
main.add_command(validate_cmd)
main.add_command(list_cmd)
main.add_command(docs_cmd)


if __name__ == "__main__":
    main()
