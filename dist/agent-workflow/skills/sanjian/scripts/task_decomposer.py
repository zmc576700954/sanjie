"""Decompose refactoring tasks into ordered subtasks."""
import os
from typing import List


def decompose(task_context: str, target_files: List[str]) -> dict:
    """
    Split a refactoring task into subtasks with dependency ordering.

    Args:
        task_context: Description of what needs to be refactored
        target_files: List of file paths to operate on

    Returns:
        {subtasks, execution_order, summary}
    """
    subtasks = []

    for idx, filepath in enumerate(target_files):
        subtask_id = f"subtask_{idx + 1}"

        # Determine operation type from context
        if any(k in task_context for k in ["rewrite", "overhaul", "rebuild", "重写", "彻底", "颠覆"]):
            operation = "REWRITE"
        elif any(k in task_context for k in ["integrate", "merge", "unify", "整合", "合并", "统一"]):
            operation = "INTEGRATE"
        else:
            operation = "RESTRUCTURE"

        # Determine scope level from context
        if any(k in task_context for k in ["cross-module", "global", "底层", "跨模块", "全局"]):
            scope_level = "DEEP"
        elif any(k in task_context for k in ["interface", "dependency", "接口", "依赖"]):
            scope_level = "BOUNDARY"
        else:
            scope_level = "SAFE"

        subtasks.append({
            "id": subtask_id,
            "target_file": filepath,
            "operation": operation,
            "description": f"{operation} on {os.path.basename(filepath)}",
            "dependencies": [f"subtask_{idx}"] if idx > 0 else [],
            "scope_level": scope_level,
        })

    execution_order = [s["id"] for s in subtasks]

    return {
        "subtasks": subtasks,
        "execution_order": execution_order,
        "summary": f"Decomposed into {len(subtasks)} subtasks, operation: {subtasks[0]['operation'] if subtasks else 'N/A'}",
    }
