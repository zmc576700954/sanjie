"""Wrappers for code modification tools from skills/tool_nezha/."""
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from skills.tool_nezha.scripts.demon_hunt import demon_hunt as _demon_hunt
from skills.tool_nezha.scripts.lotus_body import lotus_body as _lotus_body
from skills.tool_nezha.scripts.assignment_planner import create_assignment_plan as _create_plan
from skills.tool_nezha.scripts.workload_assessor import assess_workload as _assess_workload


def demon_hunt(
    target: str,
    mode: str = "bug_hunt",
    head_type: str = "cognitive",
    context: str = "",
) -> str:
    """Run Nezha's demon_hunt investigation on a target.

    Args:
        target: Target file path, code snippet, or problem description.
        mode: bug_hunt | code_review | suspicious_scan
        head_type: business | code | cognitive
        context: Optional context (requirements, history, other persona reports).
    """
    return _demon_hunt(target=target, mode=mode, head_type=head_type, context=context)


def lotus_body(
    task: str,
    arm_type: str = "main",
    scope_limit: list[str] | None = None,
    safety_level: str = "standard",
) -> str:
    """Run Nezha's lotus_body code modification.

    Args:
        task: The modification task description.
        arm_type: main | left | right
        scope_limit: Allowed file modification scope.
        safety_level: strict | standard | aggressive
    """
    return _lotus_body(task=task, arm_type=arm_type, scope_limit=scope_limit, safety_level=safety_level)


def create_assignment_plan(
    mode: str,
    target_files: list[str],
    task_description: str,
    auxiliary_head: str | None = None,
) -> dict:
    """Create a pre-execution assignment plan for Nezha's Three Heads Six Arms.

    Args:
        mode: single_head | dual_head | trinity_six_arms
        target_files: List of files involved.
        task_description: Description of the task.
        auxiliary_head: For dual_head mode: business_head or code_head.
    """
    return _create_plan(
        mode=mode,
        target_files=target_files,
        task_description=task_description,
        auxiliary_head=auxiliary_head,
    )


def assess_workload(
    file_count: int,
    line_change_est: int,
    complexity: str,
    risk_level: str,
) -> str:
    """Assess workload to determine execution mode.

    Args:
        file_count: Number of files involved.
        line_change_est: Estimated lines of change.
        complexity: simple | moderate | complex
        risk_level: low | medium | high | critical

    Returns:
        Execution mode string: single_head | dual_head | trinity_six_arms
    """
    mode = _assess_workload(
        file_count=file_count,
        line_change_est=line_change_est,
        complexity=complexity,
        risk_level=risk_level,
    )
    return mode.value
