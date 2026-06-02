"""Wrappers for code analysis tools from skills/."""
import os
import sys

# Ensure project root is in path for skills/ imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from skills.tool_tianyan.scripts.logic_tracer import trace_error as _trace_error
from skills.tool_tianyan.scripts.cross_verifier import verify_logic as _cross_verify
from skills.tool_wanglingguan.scripts.semantic_analyzer import detect_complexity as _detect_complexity


def trace_error(error_desc: str, log_file: str = None, source_code_context: str = "") -> str:
    """Trace an error through code context."""
    return _trace_error(error_desc, log_file, source_code_context)


def cross_verify(local_logic: str, official_spec: str) -> str:
    """Cross-verify local logic against an official specification."""
    return _cross_verify(local_logic, official_spec)


def analyze_complexity(file_path: str) -> dict:
    """Analyze cyclomatic complexity of functions in a Python file."""
    return _detect_complexity(file_path)
