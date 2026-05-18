# Agent Workflow

English | [中文](README_CN.md)

Risk-graduated AI coding agent with hot-pluggable skill system. Install skills into your AI coding tool, and the agent automatically discovers and uses them with appropriate safety guardrails.

## Features

- **Hot-pluggable skills** — install a skill, agent uses it immediately
- **Risk graduation** — different safety levels for different operation types
- **Cross-platform** — Claude Code, Cursor, Codex, Trae
- **Zero dependencies** — Python stdlib only
- **One-click install** — single command to set up for your platform

## Quick Start

```bash
git clone https://github.com/yourname/agent-workflow.git
cd agent-workflow

# Install for your platform
python install.py --platform claude-code
python install.py --platform cursor
python install.py --platform codex
python install.py --platform trae

# Or install a single skill
python install.py --skill sanjian --platform claude-code
```

## Skills

| Skill | Purpose | Risk Level |
|-------|---------|-----------|
| `tianyan` | Investigation & logic tracing (no code modification) | None |
| `bajiu_xuangong` | Task routing & difficulty assessment (no side effects) | None |
| `yindan` | Precision single-point fix with validation | Low |
| `taie` | Standard feature development with regression checks | Medium |
| `sanjian` | Multi-file refactoring with scope control | High |
| `kaishan` | Bulk destructive operations with logging | Critical |

## How It Works

```
User Request
    ↓
Agent (YangJian)
├── Inherent: tianyan (investigate first, always)
├── Discovers installed skills from library
├── Routes by difficulty (bajiu_xuangong)
└── Executes matched skill with safety guardrails
    ↓
Result
```

The agent does not hardcode which skills are available. It discovers them at runtime from your installed skill library. Install new skills, and they become available immediately.

## Platform Support

| Platform | Skills Location | Agent/Rules Location | Install Command |
|----------|----------------|---------------------|-----------------|
| Claude Code | `~/.claude/skills/` | `~/.claude/agents/` | `python install.py --platform claude-code` |
| Cursor | `~/.cursor/skills/` | `~/.cursor/agents/` | `python install.py --platform cursor` |
| Codex | `~/.agents/skills/` | Root `AGENTS.md` | `python install.py --platform codex` |
| Trae | `.trae/skills/` | `.trae/rules/` | `python install.py --platform trae` |

## Manual Installation

```bash
# Skills (adjust target path for your platform)
cp -r skills/tianyan ~/.claude/skills/
cp -r skills/sanjian ~/.claude/skills/

# Agent definition
cp platforms/claude-code/agents/yangjian.md ~/.claude/agents/
```

## Project Structure

```
agent-workflow/
├── skills/                  Skill packages (SKILL.md + scripts/)
│   ├── tianyan/             Investigation & logic tracing
│   ├── bajiu_xuangong/      Task routing & difficulty assessment
│   ├── sanjian/             Multi-file refactoring
│   ├── yindan/              Precision fix
│   ├── taie/                Standard feature development
│   └── kaishan/             Bulk destructive operations
├── platforms/               Platform-specific agent definitions
│   ├── claude-code/agents/
│   ├── cursor/agents/
│   ├── codex/
│   └── trae/rules/
├── docs/                    Architecture & contributing guides
├── tests/                   Mechanism tests
├── install.py               Cross-platform installer
└── pyproject.toml           Python project config
```

## Development

```bash
# Run all tests
python -m pytest tests -q

# Run skills scripts tests
python -m tests.test_skills_scripts
```

## Creating Custom Skills

Each skill is a self-contained directory:

```
my-skill/
├── SKILL.md          # AI execution instructions (required)
├── scripts/          # Deterministic tool scripts
│   └── my_tool.py
└── references/       # On-demand reference material (optional)
    └── patterns.md
```

SKILL.md format:

```markdown
---
name: my-skill
description: >
  Use when [trigger condition].
  Handles [capabilities].
---

# Skill Title

## Workflow

1. Step one...
2. Step two...

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/my_tool.py` | Does X | `param1`, `param2` | `{result}` |

## Rules

- Constraint one
- Constraint two
```

Install your custom skill:
```bash
python install.py --skill my-skill --platform claude-code
```

## Contributing

See [docs/contributing.md](docs/contributing.md) for guidelines.

## License

See [LICENSE](LICENSE).
