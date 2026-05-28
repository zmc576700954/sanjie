"""Output Schema validator for YangJian's structured output.

Parses the text output of YangJian persona and validates
that all required fields are present and correctly formatted.
"""

import re
from typing import Dict, List, Optional

REQUIRED_FIELDS = ["task_status", "output_summary", "capability_used", "tags"]
VALID_STATUSES = {"completed", "failed", "needs_clarification"}
VALID_CAPABILITIES = {"investigation", "task_routing", "security_audit"}


def validate_output(output: str) -> dict:
    """Validate YangJian output against Output Schema.

    Returns:
        {
            "valid": bool,
            "errors": [str],       # blocking issues
            "warnings": [str],     # non-blocking suggestions
            "parsed": {field: value}  # extracted fields
        }
    """
    errors = []
    warnings = []
    parsed = {}

    # Extract all [field]: value pairs
    for match in re.finditer(r"\[([^\]]+)\]:\s*(.+?)(?:\n|$)", output):
        field = match.group(1).strip()
        value = match.group(2).strip()
        parsed[field] = value

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in parsed:
            errors.append(f"Missing required field: [{field}]")
        elif not parsed[field]:
            errors.append(f"Empty value for required field: [{field}]")

    # Validate task_status enum
    if "task_status" in parsed:
        status = parsed["task_status"].lower().strip()
        if status not in VALID_STATUSES:
            errors.append(f"Invalid task_status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}")

    # Validate capability_used enum
    if "capability_used" in parsed:
        cap = parsed["capability_used"].lower().strip()
        if cap not in VALID_CAPABILITIES:
            errors.append(f"Invalid capability_used '{cap}'. Must be one of: {', '.join(VALID_CAPABILITIES)}")

    # Validate next_action format (warning only)
    if "next_action" in parsed:
        na = parsed["next_action"]
        if "capability:" not in na and "no security" not in na.lower():
            warnings.append(f"[next_action] missing 'capability:' format: {na[:60]}")

    # Validate tags non-empty
    if "tags" in parsed and not parsed["tags"].strip():
        warnings.append("[tags] is empty")

    # Check for boundary_checks format if present
    if "boundary_checks" in output:
        bc_ids = re.findall(r"id:\s*(BC-\d+)", output)
        if not bc_ids:
            warnings.append("[boundary_checks] section found but no BC-XXX IDs detected")

    # Check for security_audit format if present
    if "security_audit" in output:
        sa_ids = re.findall(r"id:\s*(SA-\d+)", output)
        if not sa_ids:
            warnings.append("[security_audit] section found but no SA-XXX IDs detected")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "parsed": parsed,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = sys.stdin.read()
    result = validate_output(content)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
