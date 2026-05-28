---
name: bajiu
description: >
  Use when a task is ambiguous and the user is UNDECIDED about which tool or approach to use.
  Scans available skills, evaluates task complexity, and outputs a structured execution plan.
  No side effects — analysis only.
  NOT for: tasks where the user already knows the operation type (use the corresponding skill directly).
  NOT for: algorithm analysis, learning plans, time complexity evaluation, or non-code planning.
  NOT for: simple questions, git operations, file listing, or casual conversation.
  Trigger ONLY when the user explicitly asks "which tool", "how to approach", "evaluate difficulty",
  "break down task", "prioritize issues", or expresses genuine uncertainty about method choice.
trigger_keywords:
  high_confidence:
    - "哪个工具"
    - "该用什么"
    - "怎么处理这个任务"
    - "帮我评估难度"
    - "which tool"
    - "how to approach"
    - "break down task"
    - "triage"
    - "prioritize issues"
    - "execution plan"
    - "任务拆解"
    - "排个优先级"
    - "不确定用什么方式"
    - "不知道从哪开始"
    - "分几步"
    - "先后顺序"
  medium_confidence:
    - "评估"
    - "规划"
    - "计划"
    - "复杂度"
    - "工作量"
    - "难度"
    - "assess"
    - "plan"
    - "complexity"
    - "workload"
    - "evaluate"
  requires_context:
    - "评估" → only when context is about code tasks (not algorithms, learning, etc.)
    - "规划" → only when context involves code/tool selection (not life/study plans)
    - "计划" → only when context involves development tasks (not learning schedules)
negative_keywords:
  - "重构"
  - "refactor"
  - "删除"
  - "delete"
  - "修复"
  - "fix"
  - "安全"
  - "security"
  - "文档"
  - "document"
  - "实现"
  - "implement"
  - "开发"
  - "develop"
tools:
  - name: skill_scanner
    script: "scripts/skill_scanner.py"
    parameters:
      skill_library: "SkillLibrary instance."
  - name: task_analyzer
    script: "scripts/task_analyzer.py"
    parameters:
      task_context: "Task description or handoff report."
      skill_profiles: "List of skill profiles."
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
