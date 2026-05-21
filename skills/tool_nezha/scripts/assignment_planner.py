"""Pre-execution assignment planner for Nezha's Three Heads Six Arms."""
from enum import Enum
from typing import Optional


class HeadRole(str, Enum):
    CONTEXT_MASTER = "context_master"
    BUSINESS_ANALYZER = "business_analyzer"
    CODE_ANALYZER = "code_analyzer"


class ArmAssignment(str, Enum):
    MAIN_ARMS = "main_arms"
    LEFT_ARMS = "left_arms"
    RIGHT_ARMS = "right_arms"


def create_assignment_plan(
    mode: str,
    target_files: list[str],
    task_description: str,
    auxiliary_head: Optional[str] = None,
) -> dict:
    """Create a pre-execution assignment plan.

    Args:
        mode: "single_head" | "dual_head" | "trinity_six_arms".
        target_files: List of files involved.
        task_description: Description of the task.
        auxiliary_head: For dual_head mode, which auxiliary head to use ("business_head" or "code_head").

    Returns:
        Assignment plan dict.
    """
    plan = {
        "mode": mode,
        "assessment_reason": task_description,
    }

    if mode == "single_head":
        return plan

    if mode == "dual_head":
        aux = auxiliary_head or "code_head"
        plan["head_assignments"] = {
            "cognitive_head": {
                "role": HeadRole.CONTEXT_MASTER.value,
                "tasks": ["Parse context", "Identify logic paths", "Final synthesis"],
                "deliverable": "[synthesis]",
            },
            aux: {
                "role": HeadRole.CODE_ANALYZER.value if aux == "code_head" else HeadRole.BUSINESS_ANALYZER.value,
                "tasks": ["Analyze target domain"],
                "deliverable": "[analysis]",
            },
        }
        return plan

    if mode == "trinity_six_arms":
        # Distribute files across three arms without overlap
        file_count = len(target_files)
        main_count = max(1, file_count // 3 + (1 if file_count % 3 > 0 else 0))
        left_count = max(1, file_count // 3 + (1 if file_count % 3 > 1 else 0))

        main_files = target_files[:main_count]
        left_files = target_files[main_count:main_count + left_count]
        right_files = target_files[main_count + left_count:]
        if not right_files:
            right_files = [left_files.pop()] if len(left_files) > 1 else main_files[:1]

        plan["head_assignments"] = {
            "cognitive_head": {
                "role": HeadRole.CONTEXT_MASTER.value,
                "tasks": [
                    "Parse global business context",
                    "Identify core vs secondary logic paths",
                    "Final root cause confirmation and priority sorting",
                ],
                "deliverable": "[synthesis] + [priority_matrix]",
            },
            "business_head": {
                "role": HeadRole.BUSINESS_ANALYZER.value,
                "tasks": [
                    "Map business rules and boundary conditions",
                    "Verify requirement compliance",
                    "Identify exception flows and missing data validation",
                ],
                "deliverable": "[business_risk] + [boundary_scenarios]",
            },
            "code_head": {
                "role": HeadRole.CODE_ANALYZER.value,
                "tasks": [
                    "AST structure analysis",
                    "Dependency chain tracing",
                    "Bug pattern matching and security scanning",
                ],
                "deliverable": "[code_risk] + [dependency_map]",
            },
        }

        plan["arm_assignments"] = {
            "main_arms": {
                "head": "cognitive_head",
                "scope": "Core logic files",
                "files": main_files,
                "task_type": "critical_fix",
                "description": "Fix root cause in core business logic",
                "dependencies": [],
            },
            "left_arms": {
                "head": "business_head",
                "scope": "Secondary business logic + boundary handling",
                "files": left_files,
                "task_type": "boundary_handling",
                "description": "Add boundary conditions, adjust defaults, improve exception handling",
                "dependencies": ["main_arms"],
            },
            "right_arms": {
                "head": "code_head",
                "scope": "Code structure optimization",
                "files": right_files,
                "task_type": "structural_optimize",
                "description": "Optimize imports, fix type hints, supplement unit tests",
                "dependencies": ["main_arms"],
            },
        }

        plan["execution_order"] = [
            {"phase": 1, "arms": ["main_arms"], "parallel": False},
            {"phase": 2, "arms": ["left_arms", "right_arms"], "parallel": True},
        ]

        plan["conflict_prevention"] = [
            "All arms' files are declared before execution, no overlapping regions",
            "If cross-file dependencies exist, auto-serialize",
            "Execution order: main_arms -> left_arms + right_arms (parallel)",
        ]

    return plan
