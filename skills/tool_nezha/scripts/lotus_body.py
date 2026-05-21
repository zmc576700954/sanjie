"""Nezha Lotus Body — single-arm execution tool.

L1 (Claude Code) orchestrates multi-arm parallelism by calling this tool
multiple times with different arm_type values.
"""
import json
from datetime import datetime, timezone

from skills.tool_bajiu.scripts.providers import get_available_provider


_PROMPTS = {
    "main": """You are Nezha's Main Arms (灵珠头控制). Execute the core logic modification.

Task: {task}
Scope Limit: {scope_limit}
Safety Level: {safety_level}

Output a JSON object with:
- execution_plan: list of tasks with id, priority, target_file, line_range, change_type, description
- execution_result: list of results with id, status, diff_summary, files_modified
- verification_checklist: list of verification items

Focus on the critical path. Be surgical and precise.""",

    "left": """You are Nezha's Left Arms (妖魔头控制). Execute secondary business logic and boundary handling.

Task: {task}
Scope Limit: {scope_limit}
Safety Level: {safety_level}

Output a JSON object with:
- execution_plan: list of tasks with id, priority, target_file, line_range, change_type, description
- execution_result: list of results with id, status, diff_summary, files_modified
- verification_checklist: list of verification items

Focus on boundary conditions, defaults, and exception handling.""",

    "right": """You are Nezha's Right Arms (除魔头控制). Execute code structure optimization.

Task: {task}
Scope Limit: {scope_limit}
Safety Level: {safety_level}

Output a JSON object with:
- execution_plan: list of tasks with id, priority, target_file, line_range, change_type, description
- execution_result: list of results with id, status, diff_summary, files_modified
- verification_checklist: list of verification items

Focus on imports, type hints, formatting, and tests.""",
}


def _call_ai(system_prompt: str, user_prompt: str) -> dict:
    """Call AI provider and parse JSON response."""
    provider = get_available_provider()
    if provider is None:
        return {}
    try:
        raw = provider.infer(system_prompt, user_prompt, timeout=10.0)
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except Exception:
        return {}


def lotus_body(
    task: str,
    arm_type: str = "main",
    scope_limit: list = None,
    safety_level: str = "standard",
) -> str:
    """Execute single-arm modification.

    Args:
        task: The modification task description.
        arm_type: "main" | "left" | "right". L1 decides which to call.
        scope_limit: Allowed file modification scope.
        safety_level: "strict" | "standard" | "aggressive".

    Returns:
        Structured execution output in [block_name]: value format.
    """
    prompt = _PROMPTS.get(arm_type, _PROMPTS["main"])
    result = _call_ai(
        prompt.format(
            task=task,
            scope_limit=scope_limit or ["all files"],
            safety_level=safety_level,
        ),
        f"Execute from {arm_type} arm perspective.",
    )

    if not result:
        result = {
            "execution_plan": [{"id": "EP-001", "priority": "P1", "description": "Fallback — no AI provider available"}],
            "execution_result": [{"id": "EP-001", "status": "partial", "diff_summary": "Unable to execute without AI provider"}],
            "verification_checklist": ["[ ] Verify changes manually"],
        }

    return _format_output(result, arm_type)


def _format_output(data: dict, arm_type: str) -> str:
    """Format output in [block_name]: value format per SPEC.md."""
    lines = [
        "[task_status]: completed",
        f'[output_summary]: Executed {len(data.get("execution_plan", []))} tasks from {arm_type} arm perspective',
        "[capability_used]: problem_solving",
        f'[tags]: fix, {arm_type}',
        "",
        f"[lotus_body_result]: arm_type={arm_type}",
        "",
        "[execution_plan]:",
    ]
    for ep in data.get("execution_plan", []):
        lines.append(f"  - id: {ep.get('id', 'EP-001')}")
        lines.append(f'    priority: {ep.get("priority", "P1")}')
        lines.append(f'    target_file: "{ep.get("target_file", "")}"')
        lines.append(f'    line_range: "{ep.get("line_range", "")}"')
        lines.append(f'    change_type: {ep.get("change_type", "fix")}')
        lines.append(f'    description: "{ep.get("description", "")}"')

    lines.append("")
    lines.append("[execution_result]:")
    for er in data.get("execution_result", []):
        lines.append(f"  - id: {er.get('id', 'EP-001')}")
        lines.append(f'    status: {er.get("status", "pending")}')
        lines.append(f'    diff_summary: "{er.get("diff_summary", "")}"')
        files = er.get("files_modified", [])
        lines.append(f'    files_modified: {files}')

    lines.append("")
    lines.append("[verification_checklist]:")
    for item in data.get("verification_checklist", []):
        lines.append(f"  - {item}")

    lines.append("")
    lines.append("[next_action]: If other arm perspectives are needed, call lotus_body with corresponding arm_type. Otherwise verify changes.")
    lines.append("[persona_handoff]:")
    lines.append('  recommended_executor: "execution-capable-persona"')
    lines.append(f'  context_summary: "Executed {len(data.get("execution_plan", []))} tasks from {arm_type} arm"')

    return "\n".join(lines)
