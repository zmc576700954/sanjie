# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`agents-develop` is a Python package providing AI-powered code investigation, fixing, and review capabilities. It implements the "Three Realms" (三界) protocol — a multi-agent collaboration system where specialized SubAgents (Investigator, Fixer, Reviewer, Documenter) handle different aspects of code analysis.

The project has two layers:
- **v2.0 Python package** (`src/agents_develop/`): Installable CLI + SDK with orchestrator and SubAgent pattern
- **Three Realms protocol** (`agents/`, `skills/`): Persona templates and skill definitions for L1 runtimes (Claude Code, Cursor, Codex)

## Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_base.py -v

# Run a single test
pytest tests/test_base.py::test_name -v

# CLI usage
agents --help
agents investigate "error description" --file auth.py
agents fix "bug description" --file session.py --review
agents review src/auth.py --type security
agents pipeline "error" --file auth.py
```

## Architecture

### Core Package (`src/agents_develop/`)

```
CLI (cli.py) → Orchestrator (orchestrator.py) → SubAgents (agents/*.py)
                     ↓
              LLMClient (llm_client.py)  ← Anthropic/OpenAI abstraction
                     ↓
              Tools (tools/*.py)  ← Code analysis, security scanning
```

**Orchestrator** routes and chains SubAgents with:
- Sequential pipelines (investigate → fix → review)
- Parallel fan-out for multi-file review
- Error-aware degradation (partial failures don't block pipeline)
- Agent handoff protocol for structured context passing

**SubAgent base** (`base.py`) implements 3-layer error handling:
1. **Tool-level**: Tool errors fed back to LLM for self-correction
2. **Node-level**: LLM call failures retry with exponential backoff (3 attempts)
3. **Global**: Circuit breaker trips after 5 consecutive failures

**Token budget** controls cost across entire pipeline (default 200k tokens).

### SubAgent Implementations

Each SubAgent in `agents/` extends `SubAgent` base class and defines:
- `system_prompt()`: Loaded from `prompts/*.md` files
- `tools()`: Tool definitions with JSON Schema
- `input_schema()` / `output_schema()`: Pydantic models for I/O

| Agent | Purpose | Tools |
|-------|---------|-------|
| Investigator | Diagnose errors, trace root causes | trace_error, cross_verify, analyze_complexity |
| Fixer | Apply code fixes | demon_hunt (scan), lotus_body (patch) |
| Reviewer | Security/quality review | security_scan, semantic_analyzer |
| Documenter | Generate structured docs | GSSC pipeline tools |

### LLM Client (`llm_client.py`)

Unified interface supporting:
- **Anthropic**: Claude models (default: claude-sonnet-4-20250514)
- **OpenAI**: GPT models (default: gpt-4o)

Returns `LLMResponse` with content, stop_reason, and tool_calls.

### Schemas (`schemas.py`)

All I/O uses Pydantic v2 models:
- `InvestigateInput/Output`, `FixInput/Output`, `ReviewInput/Output`, `DocumentInput/Output`
- `AgentHandoff`: Structured context passing between agents
- `TokenBudget`: Cost control with `remaining()`, `check()`, `record()`
- `TracingSpan`: Observability for agent/tool execution
- `PipelineResult`: Aggregated pipeline results

## Three Realms Protocol

The `agents/*.md` files define persona templates following SPEC.md conventions:

**Key principles:**
- **Decentralized routing**: L1 runtime (Claude Code) scans Capability Registry and matches by tags
- **No workflow steps**: Personas describe behavior, not sequence
- **Structured handoff**: Output uses `[block_name]: value` format for L1 parsing
- **Capability-based discovery**: Match by domain + tags, not hardcoded names

**Required Persona sections:**
1. Capability Registry (domain, tags, confidence)
2. Core Directives (behavioral guidance)
3. Output Schema (standardized blocks)

## Skills (`skills/tool_*/`)

Each skill is a SKILL.md + scripts/ directory:
- **SKILL.md**: Trigger keywords, tool definitions, routing rules
- **scripts/**: Deterministic Python scripts (CLI-first, JSON I/O)

Skills are workflow-based (same input → same output), not decentralized.

## MCP Servers (`mcp-servers/`)

MCP servers for Claude Code integration:
- `taibai_server.py`: Documentation generation
- `tianyan_server.py`: Investigation tools
- `wanglingguan_server.py`: Review/audit tools
- `yindan_server.py`: Text processing tools

## Test Structure

Tests use pytest with `unittest.mock`:
- `conftest.py`: Shared fixtures (mock_llm, sample_investigate_output)
- `test_*.py`: Unit tests for each component
- Mock LLM client to avoid API calls in tests

## Key Files

- `pyproject.toml`: Package config, dependencies, CLI entry point
- `docs/SPEC.md`: Three Realms protocol specification
- `docs/SubAgent开发最佳实践方案.md`: SubAgent development best practices
- `GEMINI.md`: Three Realms engineering standards (also applies to this project)

## Important Patterns

1. **Pydantic everywhere**: All I/O schemas use Pydantic v2 with `model_dump_json()` / `model_validate_json()`
2. **Tool execution**: Tools return strings; errors are fed back to LLM as context, not exceptions
3. **Output parsing**: `_parse_output()` tries direct JSON parse, falls back to extracting from markdown code blocks
4. **Tracing**: All agent/tool executions create `TracingSpan` for observability
5. **Config**: Uses `Config.load()` from `~/.agents-develop/config.yaml` for API keys/provider

## Tech Stack

- Python 3.10+
- Pydantic v2 (I/O schemas)
- Anthropic SDK / OpenAI SDK (LLM calls)
- Click (CLI)
- pytest + pytest-mock (testing)
- tree-sitter (code analysis)
