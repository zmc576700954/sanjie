"""Aggregate execution results from subtasks."""
from typing import List


def integrate_results(execution_results: List[dict], task_context: str = "") -> dict:
    """
    Summarize all subtask execution outcomes.

    Args:
        execution_results: List of result dicts from executor/scope_guardian
        task_context: Original task description

    Returns:
        {total_subtasks, succeeded, failed, skipped, backup_files, status}
    """
    succeeded = 0
    failed = 0
    skipped = 0
    backup_files = []

    for result in execution_results:
        if result.get("action") == "HALT":
            skipped += 1
        elif result.get("success") is True:
            succeeded += 1
            if result.get("backup_path"):
                backup_files.append(result["backup_path"])
        elif result.get("success") is False:
            failed += 1
        elif result.get("action") in ("PROCEED", "EXPAND"):
            pass  # Guardian pass-through, not an execution result
        else:
            skipped += 1

    total = succeeded + failed + skipped

    if total == 0:
        status = "NO_TASKS"
    elif failed == 0 and skipped == 0:
        status = "ALL_COMPLETE"
    elif succeeded > 0:
        status = "PARTIAL"
    else:
        status = "FAILED"

    return {
        "total_subtasks": total,
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
        "backup_files": backup_files,
        "status": status,
    }
