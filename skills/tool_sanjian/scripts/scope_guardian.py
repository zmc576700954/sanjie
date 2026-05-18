"""Scope authorization control for refactoring subtasks."""


SCOPE_HIERARCHY = {"SAFE": 0, "BOUNDARY": 1, "DEEP": 2}


def check_scope(subtask: dict, current_scope: str = "SAFE", auto_approve: bool = False) -> dict:
    """
    Check if subtask scope is within current authorization.

    Args:
        subtask: {id, target_file, operation, scope_level}
        current_scope: Currently authorized scope level
        auto_approve: Skip user input (for automation/testing)

    Returns:
        {approved, authorized_scope, action}
        action: PROCEED / EXPAND / HALT
    """
    required_scope = subtask.get("scope_level", "SAFE")
    current_level = SCOPE_HIERARCHY.get(current_scope, 0)
    required_level = SCOPE_HIERARCHY.get(required_scope, 0)

    # Within authorization — proceed
    if required_level <= current_level:
        return {
            "approved": True,
            "authorized_scope": current_scope,
            "action": "PROCEED",
        }

    # Needs expansion — request approval
    if auto_approve:
        return {
            "approved": True,
            "authorized_scope": required_scope,
            "action": "EXPAND",
        }

    user_input = input(f"Scope expansion needed: {current_scope} -> {required_scope}. Approve? (y/n): ")
    if user_input.lower().strip() == 'y':
        return {
            "approved": True,
            "authorized_scope": required_scope,
            "action": "EXPAND",
        }
    else:
        return {
            "approved": False,
            "authorized_scope": current_scope,
            "action": "HALT",
        }
