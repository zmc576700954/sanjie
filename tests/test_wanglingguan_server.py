"""Integration tests for WangLingGuan MCP server tools.

These tests invoke the MCP tool functions directly (not via the MCP transport).
Uses project-local temp dirs to avoid cross-drive path issues on Windows.
"""

import importlib.util
import os
import shutil
import sys

import pytest

# Ensure pip-installed MCP SDK is found before the local mock 'mcp' package.
# The local mcp/ shadowing the SDK is a known environment issue; these tests
# exercise the server logic by importing it directly.
_pip_site_packages = next(
    (p for p in sys.path if 'site-packages' in p and 'win32' not in p),
    None
)
if _pip_site_packages and _pip_site_packages not in sys.path[:1]:
    sys.path.insert(0, _pip_site_packages)

# Import the server module directly since 'mcp-servers' has a hyphen
_server_path = os.path.join(os.path.dirname(__file__), '..', 'mcp-servers', 'wanglingguan_server.py')
spec = importlib.util.spec_from_file_location("wanglingguan_server", _server_path)
_server_module = importlib.util.module_from_spec(spec)
sys.modules["wanglingguan_server"] = _server_module
spec.loader.exec_module(_server_module)

from wanglingguan_server import (
    analyze_call_graph,
    trace_data_flow,
    scan_security_patterns,
    check_complexity,
    detect_circular_dependencies,
    verify_fix,
    create_review_ticket,
    get_review_ticket_status,
    get_review_summary,
)
from skills.tool_wanglingguan.scripts.ticket_manager import get_ticket


# Project-local temp dir to avoid cross-drive path issues on Windows
PROJECT_TMP = os.path.join(os.path.dirname(__file__), '.tmp_test')


def _project_temp_dir():
    """Create a temp directory inside the project root."""
    import uuid
    tmpdir = os.path.join(PROJECT_TMP, str(uuid.uuid4())[:8])
    os.makedirs(tmpdir, exist_ok=True)
    return tmpdir


def _cleanup_project_temp():
    """Remove all project-local temp directories."""
    if os.path.exists(PROJECT_TMP):
        shutil.rmtree(PROJECT_TMP, ignore_errors=True)


class _TempDir:
    """Context manager for project-local temporary directories."""
    def __enter__(self):
        self.path = _project_temp_dir()
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.path):
            shutil.rmtree(self.path, ignore_errors=True)
        return False


class TestMCPToolsAnalyzeCallGraph:
    def test_mcp_analyze_call_graph(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "module.py")
            with open(test_file, 'w') as f:
                f.write("def helper():\n    pass\n")
                f.write("def main():\n")
                f.write("    helper()\n")

            result = analyze_call_graph(tmpdir, "helper", include_indirect=False)
            assert "AST CALL GRAPH ANALYSIS" in result
            assert "helper" in result
            assert "Call sites found: 1" in result

    def test_mcp_analyze_call_graph_no_results(self):
        with _TempDir() as tmpdir:
            result = analyze_call_graph(tmpdir, "nonexistent", include_indirect=False)
            assert "Call sites found: 0" in result


class TestMCPToolsTraceDataFlow:
    def test_mcp_trace_data_flow(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "app.py")
            with open(test_file, 'w') as f:
                f.write("def handler():\n")
                f.write("    name = request.form['name']\n")
                f.write("    eval(name)\n")

            result = trace_data_flow(tmpdir, "request", "eval")
            assert "DATA FLOW TRACE" in result
            assert "Flows found: 1" in result
            assert "name" in result

    def test_mcp_trace_data_flow_no_results(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "safe.py")
            with open(test_file, 'w') as f:
                f.write("def safe():\n")
                f.write("    x = 1\n")
                f.write("    return x\n")

            result = trace_data_flow(tmpdir, "request", "eval")
            assert "Flows found: 0" in result


class TestMCPToolsScanSecurityPatterns:
    def test_mcp_scan_secrets(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "config.py")
            with open(test_file, 'w') as f:
                f.write("API_KEY = 'sk_test_1234567890abcdef'\n")

            result = scan_security_patterns(test_file, scan_types=["secrets"])
            assert "SECURITY SCAN REPORT" in result
            assert "hardcoded_secret" in result
            assert "CRITICAL" in result

    def test_mcp_scan_no_issues(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "safe.py")
            with open(test_file, 'w') as f:
                f.write("x = 1\n")

            result = scan_security_patterns(test_file, scan_types=["secrets", "sql_injection", "xss", "misconfiguration"])
            assert "No security issues detected" in result

    def test_mcp_scan_misconfiguration(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "settings.py")
            with open(test_file, 'w') as f:
                f.write("DEBUG = True\n")

            result = scan_security_patterns(test_file, scan_types=["misconfiguration"])
            assert "debug_enabled" in result
            assert "CRITICAL" in result


class TestMCPToolsCheckComplexity:
    def test_mcp_check_complexity_simple(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "simple.py")
            with open(test_file, 'w') as f:
                f.write("def simple():\n")
                f.write("    return 1\n")

            result = check_complexity(test_file, threshold=10)
            assert "COMPLEXITY CHECK" in result
            assert "Max complexity: 1" in result
            assert "EXCEEDS THRESHOLD" not in result

    def test_mcp_check_complexity_exceeds(self):
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "complex.py")
            with open(test_file, 'w') as f:
                f.write("def complex_func(x, y, z):\n")
                f.write("    if x:\n")
                f.write("        if y:\n")
                f.write("            if z:\n")
                f.write("                return 1\n")
                f.write("    return 0\n")

            result = check_complexity(test_file, threshold=2)
            assert "COMPLEXITY CHECK" in result
            assert "EXCEEDS THRESHOLD" in result

    def test_mcp_check_complexity_not_found(self):
        from mcp.shared.exceptions import McpError
        with pytest.raises(McpError):
            check_complexity("/nonexistent/path.py", threshold=10)


class TestMCPToolsDetectCircularDependencies:
    def test_mcp_no_circular(self):
        with _TempDir() as tmpdir:
            a_file = os.path.join(tmpdir, "A.py")
            with open(a_file, 'w') as f:
                f.write("import B\n")
            b_file = os.path.join(tmpdir, "B.py")
            with open(b_file, 'w') as f:
                f.write("# no import of A\n")

            result = detect_circular_dependencies(tmpdir, "A", "B")
            assert "CIRCULAR DEPENDENCY CHECK" in result
            assert "No circular dependency" in result

    def test_mcp_circular_detected(self):
        with _TempDir() as tmpdir:
            a_file = os.path.join(tmpdir, "A.py")
            with open(a_file, 'w') as f:
                f.write("import B\n")
            b_file = os.path.join(tmpdir, "B.py")
            with open(b_file, 'w') as f:
                f.write("import A\n")

            result = detect_circular_dependencies(tmpdir, "A", "B")
            assert "CIRCULAR DEPENDENCY DETECTED" in result


class TestMCPToolsReviewTickets:
    def test_mcp_create_and_get_ticket(self):
        result = create_review_ticket(
            target_agent="yangjian",
            target_file="src/app.py",
            assertion_type="NULL_PATH",
            severity="Critical",
            description="Missing null check at line 42",
            fix_suggestion="Add explicit null check",
            due_date=None,
        )
        assert "REVIEW TICKET CREATED" in result
        # Extract ticket ID from result
        ticket_id = None
        for line in result.split("\n"):
            if line.startswith("Ticket ID:"):
                ticket_id = line.split(":")[1].strip()
                break
        assert ticket_id is not None
        assert ticket_id.startswith("WLG-")

        # Verify ticket exists
        status_result = get_review_ticket_status(ticket_id)
        assert "TICKET STATUS" in status_result
        assert "open" in status_result

    def test_mcp_verify_fix_security_scan(self):
        # Create a ticket
        create_result = create_review_ticket(
            target_agent="yangjian",
            target_file="src/app.py",
            assertion_type="CONFIG_SAFE",
            severity="High",
            description="Debug mode enabled",
            fix_suggestion="Set DEBUG = False",
            due_date=None,
        )
        ticket_id = None
        for line in create_result.split("\n"):
            if line.startswith("Ticket ID:"):
                ticket_id = line.split(":")[1].strip()
                break

        # Create a fixed file (still has debug=true, so should fail)
        with _TempDir() as tmpdir:
            fixed_file = os.path.join(tmpdir, "settings.py")
            with open(fixed_file, 'w') as f:
                f.write("DEBUG = True\n")

            result = verify_fix(ticket_id, fixed_file, "security_scan")
            assert "FIX VERIFICATION" in result
            # Should fail because DEBUG is still True
            assert "FAILED" in result or "Ticket reopened" in result

        # Create a truly fixed file
        with _TempDir() as tmpdir:
            fixed_file = os.path.join(tmpdir, "settings.py")
            with open(fixed_file, 'w') as f:
                f.write("DEBUG = False\n")

            result = verify_fix(ticket_id, fixed_file, "security_scan")
            assert "FIX VERIFICATION" in result
            assert "PASSED" in result

    def test_mcp_get_review_summary(self):
        result = get_review_summary()
        assert "REVIEW TICKET SUMMARY" in result
        assert "Total tickets" in result
