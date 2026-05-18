# Contributing

## Two Layers

This project has two layers that serve different purposes:

1. **`skills/`** — AI prompt assets (SKILL.md + scripts). These are what AI coding tools read to understand how to perform tasks. They follow the [Agent Skills specification](https://agentskills.io/).

2. **`src/core/`** — Python runtime engine. Provides BaseAgent, SkillLibrary, Tool abstractions for programmatic use and testing.

When adding a new skill, you typically work in both layers:
- Write the SKILL.md and scripts in `skills/<name>/`
- Optionally create a Python Skill class in `src/core/skills/<name>/`

## Adding a Skill

1. Create `skills/<name>/SKILL.md` — follow existing skills as template
2. Add scripts to `skills/<name>/scripts/`
3. If runtime class needed: create `src/core/skills/<name>/<name>.py`
4. Register in `src/core/registry/components.json`
5. Add test: `tests/test_<name>_mechanisms.py`
6. Run: `python -m pytest tests -q`

## Code Style

- Python >= 3.8 syntax only
- Absolute imports: `from src.core.xxx import ...`
- All file I/O: `encoding='utf-8'`
- No external dependencies
- Scripts: no decorative output, structured return values only

## Testing

```bash
python -m pytest tests -q
```

All tests must pass before submitting changes.

## Platform Definitions

When adding a new skill, no platform changes needed — skills are cross-platform.
When modifying agent behavior, update all files in `platforms/*/`.
