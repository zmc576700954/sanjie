"""Risk assessment and user approval gate for feature development."""


def assess_risk(target_file: str, proposed_changes: str, auto_approve: bool = False) -> dict:
    """
    Evaluate modification risk and request user approval.

    Args:
        target_file: File to be modified
        proposed_changes: Description of planned changes
        auto_approve: Skip user input (for automation/testing)

    Returns:
        {approved: bool, report: str}
    """
    report = (
        f"Risk Assessment:\n"
        f"  Target: {target_file}\n"
        f"  Changes: {proposed_changes[:100]}...\n"
        f"  Potential risks:\n"
        f"  - May affect dependent business logic\n"
        f"  - May modify data model mappings\n"
    )

    if auto_approve:
        return {"approved": True, "report": report}

    # In MCP environments, interactive input is not available.
    # Return an explicit approval request for the client (IDE) to handle.
    return {
        "approved": False,
        "report": report,
        "approval_required": True,
        "message": (
            f"Risk assessment for {target_file} requires approval. "
            f"Re-run with auto_approve=True to proceed."
        ),
    }
