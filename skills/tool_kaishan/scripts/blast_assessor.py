"""Impact assessment for bulk destructive operations."""
import os
import re
from typing import List


def assess_blast_radius(directory: str, pattern: str, action_type: str = "DELETE", auto_approve: bool = False) -> dict:
    """
    Scan for affected files and request user approval.

    Args:
        directory: Target directory to scan
        pattern: Regex pattern to match files
        action_type: DELETE or REPLACE
        auto_approve: Skip user input (for automation/testing)

    Returns:
        {approved: bool, affected_files: [str]}
    """
    if not os.path.exists(directory):
        return {"approved": False, "affected_files": [], "error": f"Directory not found: {directory}"}

    affected_files: List[str] = []
    for root, _, files in os.walk(directory):
        for file in files:
            if re.search(pattern, file):
                affected_files.append(os.path.join(root, file))

    if auto_approve:
        return {"approved": True, "affected_files": affected_files}

    # In MCP environments, interactive input is not available.
    # Return an explicit approval request for the client (IDE) to handle.
    return {
        "approved": False,
        "affected_files": affected_files,
        "approval_required": True,
        "message": (
            f"Blast radius: {len(affected_files)} files match pattern '{pattern}' in {directory}. "
            f"Action: {action_type}. "
            f"Re-run with auto_approve=True to proceed."
        ),
    }
