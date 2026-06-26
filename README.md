# Agents Develop

Multi-tool agent/skill development environment with format migration.

## Architecture

This project uses a **Core + Format Separation** architecture:

- **`core/`** contains tool-agnostic logic -- base classes, registry, shared utilities
- **`formats/`** contains tool-specific templates for each supported tool
- **`migration/`** handles conversion from core components to tool-specific formats

Components (agents, skills, tools, MCP servers) are developed once against the core base classes, then automatically migrated to formats compatible with Claude Code, ZCode, Cursor, Reasionix, and MCP.

## Quick Start

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Use the CLI
agents-dev --help
```

## Directory Structure

```
agents_develop/
├── core/                  # Tool-agnostic core implementations
│   ├── shared/            # Base classes, errors, config, logging, utils
│   ├── agents/            # Agent base class
│   ├── skills/            # Skill base class
│   ├── tools/             # Tool base class
│   └── mcp_base/          # MCP server base class
├── formats/               # Tool-specific format templates
├── migration/             # Format generators, validators, exporter
├── components/            # Complete component instances
├── cli/                   # CLI interface
└── tests/                 # Test suite
```

## Development

- All core components inherit from `CoreComponent` ABC
- Use `ComponentRegistry` for component management
- Follow the design spec at `docs/superpowers/specs/`
