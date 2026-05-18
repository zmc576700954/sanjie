# Agent Workflow

Risk-graduated code changes via AI agent skills. Hot-pluggable skill system — install a skill, agent uses it automatically.

## Structure

```
skills/              Skill packages (SKILL.md + scripts/) — cross-platform, one-click install
platforms/           Platform-specific agent definitions (claude-code, cursor, codex, trae)
docs/                Architecture & contributing documentation
tests/               Mechanism tests
```

## Orchestration Rules

1. `tianyan` (investigation) executes first — no code modification before investigation.
2. `bajiu_xuangong` (router) assesses difficulty and routes to execution skill.
3. Execution skills require scope-appropriate approval:
   - TRIVIAL → `yindan` (precision fix, no extra approval)
   - MODERATE → `taie` (feature dev, regression validation)
   - COMPLEX → `sanjian` (multi-file refactoring, user approval required)
   - CRITICAL → `kaishan` (bulk destructive, user approval + logging)

## Skill Discovery

Agent does not hardcode available skills. Skills are discovered from the library at runtime. `tianyan` is the only inherent (non-removable) skill.

## Installation

```bash
python install.py --platform claude-code   # or cursor / codex / trae
python install.py --skill sanjian --platform trae  # install single skill
```

## Code Conventions

- Python >= 3.8, absolute imports, `encoding='utf-8'` on all file I/O
- No external dependencies (stdlib only)
- Scripts in `skills/*/scripts/` are deterministic tools — no decorative output

## Testing

```bash
python -m pytest tests -q
```
