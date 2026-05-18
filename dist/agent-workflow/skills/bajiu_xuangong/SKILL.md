---
name: bajiu-xuangong
description: >
  Use when a task is ambiguous and needs difficulty assessment, skill routing,
  or execution planning. Scans available skills, evaluates task complexity,
  and outputs a structured execution plan. No side effects — analysis only.
---

# Task Router & Difficulty Assessor

## Workflow

1. Scan all installed skills from the skill library (exclude self to avoid circular routing).
2. Extract 7 decision factors from task context: clarity, scope, operation-type, risk, granularity, purpose, certainty.
3. Check prerequisite conditions for each candidate skill (hard gate — fail means excluded).
4. Calculate affinity score for candidates that pass prerequisites.
5. Output execution plan with the highest-affinity skill as primary recommendation.

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/skill_scanner.py` | List installed skills with profiles | `skill_library` instance | `{total_skills, skill_profiles}` |
| `scripts/task_analyzer.py` | Assess difficulty + match candidates | `task_context`, `skill_profiles` | `{difficulty, matched_candidates, factors}` |
| `scripts/dynamic_router.py` | Generate execution plan | `task_context`, `difficulty`, `matched_candidates` | `{execution_plan, routing_summary}` |

## Difficulty Levels

| Level | Meaning | Typical routing |
|-------|---------|-----------------|
| TRIVIAL | Single-point fix, clear target | Precision fix skill |
| MODERATE | Feature-level work, 1-2 files | Standard development skill |
| COMPLEX | Multi-file refactoring, high risk | Refactoring skill (requires approval) |
| CRITICAL | Bulk destructive operation | Bulk operations skill (requires approval) |

## Rules

- Never modify files. Output is always a plan, never an execution.
- If tianyan handoff report contains `[recommended_skill]`, that takes highest priority.
- If no candidate passes prerequisites, output "UNDETERMINED" and suggest further investigation.
- Self-adaptive: automatically discovers newly installed skills without code changes.
