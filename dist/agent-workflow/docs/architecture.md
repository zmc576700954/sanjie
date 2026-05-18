# Architecture Documentation

This document describes the internal design of the agent-workflow framework. It is intended for contributors and developers extending the system.

## Core Abstractions

Hierarchy (top-down): Agent → Skill → Tool

### Tool (`src/core/tools/base.py`)

- `Tool` (abstract): declares `name`, `description`, implements `execute(*args, **kwargs)`
- `CallableTool`: wraps a Python function. Default choice for new tools.
- `CliTool`: abstract base for shell commands, subclass implements `execute`.

### Skill (`src/core/skills/base.py`)

A Skill implements four members:

| Member | Purpose |
|--------|---------|
| `name` | Key for SkillLibrary, logging |
| `description` | One-line purpose for routing decisions |
| `get_tools()` | Returns bound Tool list |
| `match(task_description) -> float` | Task matching score [0.0, 1.0] |

### SkillLibrary (`src/core/skills/library.py`)

- `register_skill` / `unregister_skill` / `get_skill` / `get_all_skills`
- `match_skills(task, threshold)` returns scored list
- Hot-pluggable: `register_skill` takes effect immediately at runtime

### Agent (`src/core/agent/base.py`)

- `BaseAgent` implements `run(task, *args, **kwargs)`
- Routes by `self.mode`: `AgentMode.STANDALONE` or `AgentMode.WORKFLOW_NODE`
- Injects `SkillLibrary` at construction, provides `add_skill` / `remove_skill`

### Registry (`src/core/registry/`)

- `components.json`: plugin manifest `{name, version, description, module, class_name}`
- `RegistryManager.install_component()`: dynamic import + instantiation via importlib

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

1. Investigation first (tianyan) — produces handoff report
2. Routing (bajiu-xuangong) — assesses difficulty, matches skill
3. Execution — routed skill runs with appropriate guardrails
4. WORKFLOW_NODE mode returns structured summary only, no side effects

## Hot-Pluggable Skill Mechanism

- Agent declares only inherent skills (tianyan for YangJian)
- All other skills discovered from SkillLibrary at runtime
- bajiu-xuangong scans library dynamically — no hardcoded skill list
- New skills become available immediately after `register_skill()`

## Directory Layout

```
skills/                    Cross-platform skill packages
├── <skill-name>/
│   ├── SKILL.md           AI execution instructions (< 500 lines)
│   ├── scripts/           Deterministic tool scripts
│   └── references/        On-demand reference material

platforms/                 Platform-specific agent definitions
├── claude-code/agents/    .claude/agents/ format
├── cursor/agents/         .cursor/agents/ format
├── codex/                 Root AGENTS.md format
└── trae/rules/            .trae/rules/ format

src/core/                  Runtime engine
├── agent/                 BaseAgent, YangJianAgent, SearchAgent
├── skills/                Skill base, SkillLibrary, skill implementations
├── tools/                 Tool base, standard tools
├── registry/              Component registry
└── workflow/              (reserved for workflow engine)
```

## Adding a New Skill

1. Create `skills/<name>/SKILL.md` with YAML frontmatter (name, description) + workflow steps
2. Add scripts to `skills/<name>/scripts/`
3. Optionally create runtime class in `src/core/skills/<name>/` inheriting from `Skill`
4. Register in `src/core/registry/components.json`
5. Add test in `tests/test_<name>_mechanisms.py`

## Adding a New Agent

1. Inherit `BaseAgent`, implement `run()` handling both STANDALONE and WORKFLOW_NODE
2. Inject inherent skills in constructor via `add_skill()`
3. Create platform definitions in `platforms/*/`
4. Register in `components.json`

## Known Constraints

- `bajiu_task_analyzer` uses keyword matching (will improve with LLM integration)
- `taie_risk_assessor` / `kaishan_blast_assessor` block on `input()` without `auto_approve=True`
- `kaishan_*` tools use `os.getcwd()` for log paths — cwd must be repo root
- Windows: use `&` not `&&` for command chaining in shell
