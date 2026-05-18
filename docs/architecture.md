# Architecture Documentation

This document describes the internal design of the Sanjie (三界) framework. It is intended for contributors and developers extending the system.

## Design Philosophy

Sanjie follows a **MCP-First, Decentralized** architecture:

- **No Central Orchestrator**: There is no `main.py` or central Python class managing agents. Each Agent and Skill is entirely decoupled.
- **Host CLI Routing**: Claude Code, Gemini CLI, Cursor, or other AI IDE hosts load the appropriate agent based on metadata.
- **Text-Based Handoff**: Agents communicate via structured markdown blocks (A2A protocol), not Python function calls.

## Core Abstractions

### Agent (`agents/*.md`)

An Agent is defined as a standalone Markdown persona file containing:

- **Personality & Role**: Judicial, strategic, or creative characterization.
- **Core Directives**: Step-by-step workflows and decision trees.
- **Celestial Protocol**: Exact tool invocation formats with few-shot examples.
- **Forbidden Actions**: Explicit boundaries on what the agent must never do.

Agents do not execute code directly. They produce structured text output that triggers tools via the host CLI.

### Skill (`skills/tool_*/`)

A Skill is a self-contained tool package with the following structure:

```
skills/tool_<name>/
├── SKILL.md          # AI execution instructions and tool schema
├── scripts/          # Deterministic Python scripts
└── references/       # Optional on-demand reference material
```

Each Skill provides atomic capabilities (e.g., context compression, logic tracing, format auditing). Scripts must:
- Accept clear CLI arguments or standard JSON input.
- Return standard JSON or Markdown output.
- Be ready for MCP server encapsulation.

### MCP Server (`mcp-servers/*.py`)

MCP Servers wrap Skill scripts into standard MCP tools that can be consumed by any modern AI IDE.

Key standards:
- Use `pydantic.Field` for exhaustive parameter descriptions.
- Raise `mcp.shared.exceptions.McpError` with proper `ErrorData` codes.
- Validate filesystem paths via `skills.utils.ensure_safe_path` to prevent traversal attacks.

### Utility (`skills/utils.py`)

Shared cross-cutting utilities used by both Skills and MCP Servers:

- `ensure_safe_path(filepath, workspace_root)`: Resolves and validates that a path is strictly within the workspace.

## Skill Risk Graduation

Skills are ordered by destructiveness, each with proportionally stronger safety mechanisms:

| Skill | Risk Level | Safety Mechanism |
|-------|-----------|-----------------|
| yindan | Lowest | Text consistency + py_compile, auto-rollback |
| taie | Medium | Risk assessment + user approval + AST regression |
| sanjian | High | Scope guardian + backup + syntax validation + rollback |
| kaishan | Highest | Blast assessment + mandatory approval + destruction logging |

## Agent Orchestration (YangJian)

The reference agent enforces:

1. **Investigation first** (tianyan) — produces handoff report
2. **Routing** (bajiu-xuangong) — assesses difficulty, matches skill
3. **Execution** — routed skill runs with appropriate guardrails
4. **Structured output** — returns standardized markdown blocks only

## Directory Layout

```
/
├── agents/                 # Agent persona definitions (Markdown)
├── mcp-servers/            # MCP standard server implementations
├── skills/                 # Atomic skill packages
│   ├── utils.py            # Shared path security and utilities
│   ├── tool_<name>/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   └── references/
│   └── celestial_registry/ # Skill discovery and registry
├── docs/                   # Documentation and memory index
│   ├── architecture.md     # This file
│   ├── MEMORY_INDEX.md     # Hot index of archived documents
│   └── archive/            # Cold storage for archived docs
├── config/                 # Configuration templates
├── install.py              # Cross-platform installation helper
├── plugin.json             # Claude Code plugin manifest
├── pyproject.toml          # Python package metadata
└── GEMINI.md               # Development protocol and discipline
```

## Adding a New Skill

1. Create `skills/<name>/SKILL.md` with YAML frontmatter (name, description) + workflow steps.
2. Add deterministic scripts to `skills/<name>/scripts/`.
3. Optionally create an MCP server wrapper in `mcp-servers/<name>_server.py`.
4. Add tests in `tests/test_<name>.py`.

## Adding a New MCP Server

1. Create `mcp-servers/<name>_server.py` using `FastMCP`.
2. Import skill scripts and wrap them as `@mcp.tool()` functions.
3. Use `skills.utils.ensure_safe_path` for any filesystem access.
4. Register the server in `plugin.json`.

## Security Considerations

- **Path Traversal**: All filesystem tools must validate paths via `ensure_safe_path`, which uses `os.path.commonpath` (safe on both Unix and Windows).
- **URL Protocols**: Web fetchers must restrict to `http://` and `https://` only.
- **Error Handling**: Tools must raise `McpError` with structured `ErrorData`, never return raw exception strings.

## Known Constraints

- `bajiu_task_analyzer` uses keyword matching (will improve with LLM integration).
- `taie_risk_assessor` / `kaishan_blast_assessor` block on `input()` without `auto_approve=True`.
- `kaishan_*` tools use `os.getcwd()` for log paths — cwd must be repo root.
- Windows: use `&` not `&&` for command chaining in shell.
