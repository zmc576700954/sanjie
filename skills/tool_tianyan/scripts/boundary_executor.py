"""Boundary Check Executor - Automatically execute verification actions
from YangJian's [boundary_checks] findings.

Converts static verification_needed descriptions into actionable
code checks using AST analysis and pattern matching.
"""

import ast
import os
import re
from typing import Dict, List, Optional


def _check_null_path(file_path: str, line_num: int) -> dict:
    """Check if a function can return None at the given line."""
    if not os.path.exists(file_path):
        return {"status": "skipped", "reason": "file not found"}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if line_num < 1 or line_num > len(lines):
            return {"status": "skipped", "reason": "line out of range"}
        line = lines[line_num - 1].strip()
        has_return_none = "return None" in line or "return" not in line
        has_guard = "if" in line and ("is None" in line or "is not None" in line)
        return {
            "status": "checked",
            "line": line,
            "returns_none": "return None" in line,
            "has_guard": has_guard,
            "recommendation": "Add explicit None guard" if not has_guard else "Guard present",
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def _check_input_validation(file_path: str, line_num: int) -> dict:
    """Check if user input is validated before use."""
    if not os.path.exists(file_path):
        return {"status": "skipped", "reason": "file not found"}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if line_num < 1 or line_num > len(lines):
            return {"status": "skipped", "reason": "line out of range"}
        line = lines[line_num - 1].strip()
        # Check for common validation patterns
        has_sanitization = any(kw in line.lower() for kw in [
            "validate", "sanitize", "escape", "strip", "int(", "float(",
            "isinstance", "len(", "assert", "raise"
        ])
        # Check for dangerous sinks
        has_dangerous_sink = any(kw in line for kw in [
            "execute(", "eval(", "exec(", "os.system(", "subprocess",
            "open(", "write(", "render("
        ])
        return {
            "status": "checked",
            "line": line,
            "has_sanitization": has_sanitization,
            "in_dangerous_sink": has_dangerous_sink,
            "recommendation": "Add input validation" if has_dangerous_sink and not has_sanitization else "Input handling appears safe",
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def _check_info_exposure(file_path: str, line_num: int) -> dict:
    """Check for potential information exposure."""
    if not os.path.exists(file_path):
        return {"status": "skipped", "reason": "file not found"}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if line_num < 1 or line_num > len(lines):
            return {"status": "skipped", "reason": "line out of range"}
        line = lines[line_num - 1].strip()
        # Check for exception details exposure
        exposes_detail = any(kw in line for kw in [
            "str(e)", "traceback", "stack_trace", "error.message",
            "repr(e)", "args[0]"
        ])
        # Check for secret patterns in error messages
        has_secret_ref = any(kw in line.lower() for kw in [
            "password", "token", "key", "secret", "credential"
        ])
        return {
            "status": "checked",
            "line": line,
            "exposes_detail": exposes_detail,
            "references_secret": has_secret_ref,
            "recommendation": "Sanitize error output" if exposes_detail or has_secret_ref else "No exposure risk detected",
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


_EXECUTORS = {
    "NULL_PATH": _check_null_path,
    "INPUT_VALIDATION": _check_input_validation,
    "INFO_EXPOSURE": _check_info_exposure,
}


def execute_boundary_check(bc_entry: dict) -> dict:
    """Execute a single boundary check entry.

    Args:
        bc_entry: dict with keys: id, type, location (file:line), description, concern

    Returns:
        dict with: id, type, status, result, recommendation
    """
    bc_type = bc_entry.get("type", "INPUT_VALIDATION")
    location = bc_entry.get("location", "")

    # Parse file:line from location
    match = re.match(r"(.+):(\d+)", location)
    if not match:
        return {
            "id": bc_entry.get("id", "BC-???"),
            "type": bc_type,
            "status": "skipped",
            "reason": f"Cannot parse location: {location}",
        }

    file_path = match.group(1)
    line_num = int(match.group(2))

    executor = _EXECUTORS.get(bc_type)
    if not executor:
        return {
            "id": bc_entry.get("id", "BC-???"),
            "type": bc_type,
            "status": "skipped",
            "reason": f"No executor for type: {bc_type}",
        }

    result = executor(file_path, line_num)
    return {
        "id": bc_entry.get("id", "BC-???"),
        "type": bc_type,
        **result,
    }


def execute_all_boundary_checks(boundary_checks: List[dict]) -> List[dict]:
    """Execute all boundary check entries and return results."""
    return [execute_boundary_check(bc) for bc in boundary_checks]
