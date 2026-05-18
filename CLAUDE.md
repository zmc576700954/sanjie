# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Read `AGENTS.md` first — it is the single source of truth for orchestration rules and conventions.

## Quick Reference

- Skills: `skills/*/SKILL.md` (cross-platform, installable)
- Scripts: `skills/*/scripts/` (deterministic tools)
- Agent definitions: `platforms/claude-code/agents/yangjian.md`
- Runtime engine: `src/core/` (BaseAgent, SkillLibrary, Tool abstractions)
- Architecture docs: `docs/architecture.md`
- Tests: `python -m pytest tests -q`

## Session Workflow

1. Read `AGENTS.md` for orchestration rules.
2. If modifying a skill, read its `skills/<name>/SKILL.md`.
3. If modifying core abstractions, read `docs/architecture.md` and `.trae/specs/`.

## Conventions

- Python >= 3.8, absolute imports, `encoding='utf-8'`
- No external dependencies
- No decorative output in scripts — structured return values only
- Validate syntax after every file write
