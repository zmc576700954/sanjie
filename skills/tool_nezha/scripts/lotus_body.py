"""Nezha Lotus Body — parallel execution with Six Arms."""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from skills.tool_bajiu.scripts.providers import get_available_provider
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode
from skills.tool_nezha.scripts.assignment_planner import create_assignment_plan


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
        return _execute_dual_arms(task, scope, safety_level, timestamp)
    else:
        return _execute_six_arms(task, scope, safety_level, timestamp)


_SINGLE_ARMS_PROMPT = """You are Nezha. Execute the following modification task precisely.

Task: {{task}}
Scope Limit: {{scope_limit}}
Safety Level: {{safety_level}}

Output a JSON object with:
- execution_plan: list of tasks with id, priority, target_file, line_range, change_type, description
- execution_result: list of results with id, status, diff_summary, files_modified
- verification_checklist: list of verification items

Be surgical and precise. Do not over-engineer."""

_DUAL_MAIN_PROMPT = """You are Nezha's Main Arms. Execute the primary modification task.

Task: {{task}}
Assigned Files: {{files}}
Scope Limit: {{scope_limit}}
Safety Level: {{safety_level}}

Output JSON with execution_plan and execution_result for your assigned files only."""

_DUAL_AUX_PROMPT = """You are Nezha's Auxiliary Arms. Execute the secondary modification task.

Task: {{task}}
Assigned Files: {{files}}
Scope Limit: {{scope_limit}}
Safety Level: {{safety_level}}

Output JSON with execution_plan and execution_result for your assigned files only."""

_MAIN_ARMS_PROMPT = """You are Nezha's Main Arms (灵珠头控制). Execute the core logic modification.

Task: {{task}}
Assigned Files: {{files}}
Scope Limit: {{scope_limit}}
Safety Level: {{safety_level}}

Output JSON with execution_plan and execution_result for your assigned files only."""

_LEFT_ARMS_PROMPT = """You are Nezha's Left Arms (妖魔头控制). Execute secondary business logic and boundary handling.

Task: {{task}}
Assigned Files: {{files}}
Scope Limit: {{scope_limit}}
Safety Level: {{safety_level}}

Output JSON with execution_plan and execution_result for your assigned files only."""

_RIGHT_ARMS_PROMPT = """You are Nezha's Right Arms (除魔头控制). Execute code structure optimization.

Task: {{task}}
Assigned Files: {{files}}
Scope Limit: {{scope_limit}}
Safety Level: {{safety_level}}

Output JSON with execution_plan and execution_result for your assigned files only."""


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


def _execute_dual_arms(task: str, scope: list, safety_level: str, timestamp: str) -> str:
    """Dual arms execution — split into two parallel tasks."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(
            _call_ai,
            _DUAL_MAIN_PROMPT.format(
                task=task,
                files=scope[:len(scope)//2] if scope else ["all"],
                scope_limit=scope or ["all files"],
                safety_level=safety_level,
            ),
            "Execute primary modifications.",
        )
        future2 = executor.submit(
            _call_ai,
            _DUAL_AUX_PROMPT.format(
                task=task,
                files=scope[len(scope)//2:] if scope else ["all"],
                scope_limit=scope or ["all files"],
                safety_level=safety_level,
            ),
            "Execute secondary modifications.",
        )
        result1 = future1.result()
        result2 = future2.result()

    combined = {
        "execution_plan": result1.get("execution_plan", []) + result2.get("execution_plan", []),
        "execution_result": result1.get("execution_result", []) + result2.get("execution_result", []),
        "verification_checklist": list(set(
            result1.get("verification_checklist", []) + result2.get("verification_checklist", [])
        )),
    }
    return _format_execution_report(combined, timestamp, "dual_head")


def _execute_six_arms(task: str, scope: list, safety_level: str, timestamp: str) -> str:
    """Six arms execution — full trinity mode with pre-execution assignment."""
    # Phase 1: Generate assignment plan
    plan = create_assignment_plan(
        mode="trinity_six_arms",
        target_files=scope if scope else ["*"],
        task_description=task,
    )

    arm_assignments = plan.get("arm_assignments", {})

    # Phase 2: Main arms execute first (phase 1)
    main_assignment = arm_assignments.get("main_arms", {})
    main_files = main_assignment.get("files", scope[:max(1, len(scope)//3)] if scope else ["all"])
    main_result = _call_ai(
        _MAIN_ARMS_PROMPT.format(
            task=task,
            files=main_files,
            scope_limit=scope or ["all files"],
            safety_level=safety_level,
        ),
        "Execute core logic modifications.",
    )

    # Phase 3: Left and right arms execute in parallel (phase 2)
    left_assignment = arm_assignments.get("left_arms", {})
    left_files = left_assignment.get("files", scope[max(1, len(scope)//3):max(2, 2*len(scope)//3)] if scope else ["all"])

    right_assignment = arm_assignments.get("right_arms", {})
    right_files = right_assignment.get("files", scope[max(2, 2*len(scope)//3):] if scope else ["all"])

    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(
            _call_ai,
            _LEFT_ARMS_PROMPT.format(
                task=task,
                files=left_files,
                scope_limit=scope or ["all files"],
                safety_level=safety_level,
            ),
            "Execute business boundary modifications.",
        )
        right_future = executor.submit(
            _call_ai,
            _RIGHT_ARMS_PROMPT.format(
                task=task,
                files=right_files,
                scope_limit=scope or ["all files"],
                safety_level=safety_level,
            ),
            "Execute structural optimization modifications.",
        )
        left_result = left_future.result()
        right_result = right_future.result()

    # Combine all results
    combined = {
        "execution_plan": (
            main_result.get("execution_plan", [])
            + left_result.get("execution_plan", [])
            + right_result.get("execution_plan", [])
        ),
        "execution_result": (
            main_result.get("execution_result", [])
            + left_result.get("execution_result", [])
            + right_result.get("execution_result", [])
        ),
        "verification_checklist": list(set(
            main_result.get("verification_checklist", [])
            + left_result.get("verification_checklist", [])
            + right_result.get("verification_checklist", [])
        )),
    }

    # Add assignment plan metadata to report
    report = _format_execution_report(combined, timestamp, "trinity_six_arms")

    # Append arm assignment summary
    assignment_summary = f"""
[arm_assignments]:
  main_arms:
    head: cognitive_head
    files: {main_files}
    task_type: critical_fix
  left_arms:
    head: business_head
    files: {left_files}
    task_type: boundary_handling
  right_arms:
    head: code_head
    files: {right_files}
    task_type: structural_optimize
"""
    return report + assignment_summary


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
