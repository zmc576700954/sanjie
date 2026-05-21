"""Nezha Lotus Body — parallel execution with Six Arms."""
import json
from datetime import datetime, timezone

from skills.tool_bajiu.scripts.providers import get_available_provider
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode


_SINGLE_ARMS_PROMPT = """You are Nezha. Execute the following modification task precisely.

Task: {{task}}
Scope Limit: {{scope_limit}}
Safety Level: {{safety_level}}

Output a JSON object with:
- execution_plan: list of tasks with id, priority, target_file, line_range, change_type, description
- execution_result: list of results with id, status, diff_summary, files_modified
- verification_checklist: list of verification items

Be surgical and precise. Do not over-engineer."""


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
    input_source: str,
    input_payload: dict,
    scope_limit: list = None,
    safety_level: str = "standard",
    file_count: int = 1,
    line_change_est: int = 0,
    complexity: str = "simple",
    risk_level: str = "low",
) -> str:
    """Execute lotus body refactoring.

    Args:
        input_source: "demon_hunt_report" | "direct_instruction" | "yangjian_handoff".
        input_payload: The report or instruction dict.
        scope_limit: Allowed file modification scope.
        safety_level: "strict" | "standard" | "aggressive".
        file_count: Number of files involved (for workload assessment).
        line_change_est: Estimated lines of change.
        complexity: "simple" | "moderate" | "complex".
        risk_level: "low" | "medium" | "high" | "critical".

    Returns:
        Structured execution report string.
    """
    execution_mode = assess_workload(file_count, line_change_est, complexity, risk_level)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    scope = scope_limit or []

    # Extract task description from payload
    if input_source == "demon_hunt_report":
        task = f"Execute fixes from report: {json.dumps(input_payload.get('suggested_fixes', []))}"
    elif input_source == "yangjian_handoff":
        task = f"Execute handoff: {input_payload.get('action', 'No action specified')}"
    else:
        task = input_payload.get("instruction", "No instruction provided")

    if execution_mode == ExecutionMode.SINGLE_HEAD:
        return _execute_single_arms(task, scope, safety_level, timestamp)
    elif execution_mode == ExecutionMode.DUAL_HEAD:
        return _execute_single_arms(task, scope, safety_level, timestamp)
    else:
        return _execute_single_arms(task, scope, safety_level, timestamp)


def _execute_single_arms(task: str, scope: list, safety_level: str, timestamp: str) -> str:
    """Single arms execution."""
    prompt = _SINGLE_ARMS_PROMPT.format(
        task=task,
        scope_limit=scope or ["all files"],
        safety_level=safety_level,
    )
    result = _call_ai(prompt, "Please generate execution plan and results.")

    if not result:
        result = {
            "execution_plan": [{"id": "EP-001", "priority": "P1", "description": "Fallback execution — no AI provider available"}],
            "execution_result": [{"id": "EP-001", "status": "partial", "diff_summary": "Unable to execute without AI provider"}],
            "verification_checklist": ["[ ] Verify changes manually"],
        }

    return _format_execution_report(result, timestamp, "single_head")


def _format_execution_report(data: dict, timestamp: str, execution_mode: str) -> str:
    """Format execution data into structured report."""
    lines = [
        "[lotus_report]:",
        f'  timestamp: "{timestamp}"',
        f'  execution_mode: "{execution_mode}"',
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

    total = len(data.get("execution_plan", []))
    success = len([er for er in data.get("execution_result", []) if er.get("status") == "success"])
    lines.append("")
    lines.append(f"  total_changes: {total}")
    lines.append(f'  success_rate: "{success}/{total}"')
    lines.append('  next_steps: "Review changes and run tests."')

    return "\n".join(lines)
