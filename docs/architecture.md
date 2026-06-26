# Architecture Overview

## Core Principle: Core + Format Separation

The agents_develop architecture separates **core functionality** from **tool-specific formats**:

```
Core Implementation (Tool-Agnostic) + Format Adapters (Tool-Specific) = Complete Component
```

This means you write your component's logic once, and the system automatically generates
the appropriate format files for each target AI development tool.

## Directory Structure

```
agents_develop/
├── core/                    # Core implementations (tool-agnostic)
│   ├── agents/              # Agent base class and registry
│   ├── skills/              # Skill base class and registry
│   ├── tools/               # Tool base class and registry
│   ├── shared/              # Shared utilities, errors, base classes
│   └── mcp_base/            # MCP server base class
├── formats/                 # Format templates for each tool
│   ├── claude/              # Claude Code/Desktop templates
│   ├── zcode/               # ZCode templates
│   ├── cursor/              # Cursor templates
│   ├── reasionix/           # Reasionix templates
│   └── mcp/                 # MCP templates
├── components/              # Component library (core + generated formats)
│   └── _example/            # Example component
├── migration/               # Migration tools (generators, validators, exporter)
│   ├── generators/          # Format generators
│   ├── validators/          # Format validators
│   └── exporter.py          # Unified exporter
├── cli/                     # CLI commands
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## Component Types and Relationships

```
CoreComponent (abstract base)
├── SkillBase        # Reusable skills with instructions + checklist
├── AgentBase        # Agents with system prompt + plan/reflect loop
└── ToolBase         # Python tools with function definitions

MCPServerBase (separate hierarchy)
└── Wraps ToolBase instances for MCP protocol
```

All component types share:
- `ComponentMetadata`: Name, type, version, description, tags, dependencies
- `execute()`: Core logic execution
- `validate_input()`: Input validation
- `configure()`: Runtime configuration
- `to_dict()`: Serialization for format generation

## Data Flow

```
Developer Workflow:

  ┌──────────┐     ┌──────────────┐     ┌──────────────────┐
  │  Create   │────>│   Generate   │────>│     Export        │
  │  Core     │     │   Formats    │     │     to Target     │
  └──────────┘     └──────────────┘     └──────────────────┘
       │                 │                       │
       v                 v                       v
  ┌──────────┐     ┌──────────────┐     ┌──────────────────┐
  │  Test     │     │   Validate   │     │     Verify in     │
  │  Core     │     │   Formats    │     │     Target Env    │
  └──────────┘     └──────────────┘     └──────────────────┘

Component Data Flow:

  ┌────────────┐     ┌─────────────┐     ┌──────────────────┐
  │  core/*.py │────>│ manifest.json│────>│ Format Generators│
  │  (logic)   │     │ (metadata)   │     │ (per-tool adapt) │
  └────────────┘     └─────────────┘     └────────┬─────────┘
                                                 │
                    ┌────────────────────────────┼────────────────┐
                    v                v            v                v
              ┌──────────┐   ┌──────────┐  ┌──────────┐   ┌──────────┐
              │ claude/  │   │ zcode/   │  │ cursor/  │   │ mcp/     │
              │ SKILL.md │   │Command.md│  │ SKILL.md │   │server.py │
              └──────────┘   └──────────┘  └──────────┘   └──────────┘
```

## Export Pipeline

The `ComponentExporter` orchestrates the full export pipeline:

1. **Check** if a generator exists for each target tool
2. **Generate** format files using the generator
3. **Write** files to the output directory
4. **Validate** generated files using the validator
5. **Report** results per tool (pass/fail with errors/warnings)

Errors are handled gracefully: if one tool fails, the others continue.
The exit code is 0 if all tools pass, 1 if any tool has errors.

## Registry Pattern

The `ComponentRegistry` is a singleton that tracks all registered components:

- `register(component)`: Add a component to the registry
- `get(name)`: Retrieve a component by name
- `list_by_type(type)`: List all components of a given type
- `list_all()`: List all registered components
- `unregister(name)`: Remove a component

## Error Hierarchy

```
AgentsDevelopError
├── ComponentError
│   ├── ComponentNotFoundError
│   ├── DuplicateComponentError
│   └── ComponentValidationError
├── MigrationError
│   ├── FormatGenerationError
│   ├── FormatValidationError
│   ├── UnsupportedToolError
│   └── TemplateError
└── ConfigError
```
