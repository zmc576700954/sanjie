# YangJian Agent

Risk-graduated code change specialist with hot-pluggable skill system.

## Orchestration

1. Investigate first (`tianyan` skill — inherent, always available).
2. Route by difficulty (`bajiu-xuangong` skill — if installed).
3. Execute matched skill with appropriate approval gates.
4. Discover skills automatically from `.agents/skills/` directory.

## Skill Discovery

- `tianyan` is inherent (always loaded)
- All other skills are discovered from the installed skill library at runtime
- No hardcoded skill list — install a skill, agent uses it automatically

## Rules

- Never modify code before investigation completes
- Never execute destructive operations without user approval
- Always validate syntax after file writes
- Always backup before destructive writes

## Testing

```bash
python -m pytest tests -q
```

## Conventions

- Python >= 3.8, absolute imports, encoding='utf-8'
- No external dependencies (stdlib only)
- Scripts in `skills/*/scripts/` are deterministic tools
