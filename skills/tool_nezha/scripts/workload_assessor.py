"""Workload assessment for Nezha's Three Heads Six Arms mode selection."""
from enum import Enum


class ExecutionMode(str, Enum):
    SINGLE_HEAD = "single_head"
    DUAL_HEAD = "dual_head"
    TRINITY_SIX_ARMS = "trinity_six_arms"


def assess_workload(
    file_count: int,
    line_change_est: int,
    complexity: str,
    risk_level: str,
) -> ExecutionMode:
    """Assess workload and select execution mode.

    Args:
        file_count: Number of files involved.
        line_change_est: Estimated lines of change.
        complexity: "simple" | "moderate" | "complex".
        risk_level: "low" | "medium" | "high" | "critical".

    Returns:
        ExecutionMode: SINGLE_HEAD, DUAL_HEAD, or TRINITY_SIX_ARMS.
    """
    if (
        file_count > 5
        or line_change_est > 200
        or complexity == "complex"
        or risk_level == "critical"
    ):
        return ExecutionMode.TRINITY_SIX_ARMS

    if (
        file_count <= 5
        and line_change_est <= 200
        and complexity == "moderate"
    ):
        return ExecutionMode.DUAL_HEAD

    return ExecutionMode.SINGLE_HEAD
