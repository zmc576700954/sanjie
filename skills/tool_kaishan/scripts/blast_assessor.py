"""Impact assessment for bulk destructive operations."""
import os
import re
from typing import List


def assess_blast_radius(
    directory: str,
    pattern: str,
    action_type: str = "DELETE",
    auto_approve: bool = False,
    max_depth: int = 0,
) -> dict:
    """
    Scan for affected files and request user approval.

    Args:
        directory: Target directory to scan.
        pattern: Regex pattern to match file names.
        action_type: DELETE or REPLACE.
        auto_approve: Skip user input (for automation/testing).
        max_depth: Maximum directory recursion depth. 0 means unlimited.
                   Useful to prevent runaway scans on symlink loops or
                   extremely deep trees.

    Returns:
        {approved: bool, affected_files: [str]}
    """
    if not os.path.exists(directory):
        return {"approved": False, "affected_files": [], "error": f"Directory not found: {directory}"}

    if not os.path.isdir(directory):
        return {"approved": False, "affected_files": [], "error": f"Not a directory: {directory}"}

    # Pre-compile regex so invalid patterns fail fast with a clear message
    try:
        compiled = re.compile(pattern)
    except re.error as e:
        return {"approved": False, "affected_files": [], "error": f"Invalid regex pattern: {e}"}

    affected_files: List[str] = []
    for root, dirs, files in os.walk(directory, followlinks=False):
        # Depth limiting: count separators relative to the base directory
        if max_depth > 0:
            depth = root.replace(directory, "").count(os.sep)
            if depth >= max_depth:
                dirs.clear()  # stop descending further
                continue

        for file in files:
            if compiled.search(file):
                affected_files.append(os.path.join(root, file))

    affected_files.sort()

    if auto_approve:
        return {"approved": True, "affected_files": affected_files}

    return {
        "approved": False,
        "affected_files": affected_files,
        "approval_required": True,
        "message": (
            f"Blast radius: {len(affected_files)} files match pattern "
            f"'{pattern}' in {directory}. Action: {action_type}. "
            f"Re-run with auto_approve=True to proceed."
        ),
    }
