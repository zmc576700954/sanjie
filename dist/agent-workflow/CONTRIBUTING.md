# Contributing

## Two Layers

1. **`skills/`** — AI prompt assets (SKILL.md + scripts). Follow the [Agent Skills specification](https://agentskills.io/).
2. **`tests/`** — Functional tests for all scripts.

## Adding a Skill

1. Create `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`) + workflow steps.
2. Add scripts to `skills/<name>/scripts/`.
3. Add `__init__.py` to `skills/<name>/` and `skills/<name>/scripts/`.
4. Add tests in `tests/test_skills_scripts.py` or a new test file.
5. Run: `python -m pytest tests -q`

## Code Style

- Python >= 3.8 syntax only
- All file I/O: `encoding='utf-8'`
- No external dependencies
- Scripts: structured return values, no decorative output

## Testing

```bash
python -m pytest tests -q
```

All tests must pass before submitting.

## Platform Definitions

Skills are cross-platform — no platform changes needed when adding a skill.
When modifying agent behavior, update all files in `platforms/*/`.
