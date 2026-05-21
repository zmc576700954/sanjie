"""End-to-end integration tests for WangLingGuan enhanced review pipeline.

These tests validate the complete multi-layer review + closed-loop ticket workflow.
"""

import os
import sys
import tempfile
import shutil
import uuid

import pytest

# Import all components
from skills.tool_wanglingguan.scripts.semantic_analyzer import (
    analyze_call_graph,
    extract_dependencies,
    detect_complexity,
    trace_data_flow,
    find_dead_code,
)
from skills.tool_wanglingguan.scripts.security_scanner import (
    scan_secrets,
    scan_sql_injection,
    scan_xss_vectors,
    scan_misconfiguration,
    scan_dangerous_operations,
)
from skills.tool_wanglingguan.scripts.format_auditor import (
    audit_content,
    validate_yaml_schema,
    check_markdown_links,
)
from skills.tool_wanglingguan.scripts.import_validator import (
    verify_dependency_direction,
    detect_circular_dependencies,
    verify_forbidden_dependency,
)
from skills.tool_wanglingguan.scripts.ticket_manager import (
    create_ticket,
    get_ticket,
    update_ticket_status,
    list_tickets,
    get_ticket_summary,
    TICKET_DIR,
)
from skills.tool_wanglingguan.scripts.code_caller_tracer import (
    find_callers,
    check_null_handling,
)


PROJECT_TMP = os.path.join(os.path.dirname(__file__), '.tmp_integration')


def _project_temp_dir():
    tmpdir = os.path.join(PROJECT_TMP, str(uuid.uuid4())[:8])
    os.makedirs(tmpdir, exist_ok=True)
    return tmpdir


def _cleanup():
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


# ───────────────────────────────────────────────
# Test 1: End-to-End Multi-Layer Review
# ───────────────────────────────────────────────

class TestEndToEndReview:
    """Simulates a complete WangLingGuan review workflow."""

    def test_layer_1_format_compliance(self):
        """Layer 1: Validate document format."""
        doc = "---\ntitle: Spec\ndate: 2024-01-01\nstatus: draft\n---\n# Body"
        result = audit_content(doc, 'document')
        assert result['status'] == 'PASS'

        # Missing key
        bad_doc = "---\ntitle: Spec\n---\n# Body"
        result = audit_content(bad_doc, 'document')
        assert result['status'] == 'FAIL'

    def test_layer_2_quality_metrics(self):
        """Layer 2: Check code complexity as quality metric."""
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "code.py")
            with open(test_file, 'w') as f:
                f.write("def simple():\n")
                f.write("    return 1\n")
                f.write("def complex(x, y, z):\n")
                f.write("    if x:\n")
                f.write("        if y:\n")
                f.write("            if z:\n")
                f.write("                for i in range(10):\n")
                f.write("                    if i > 5:\n")
                f.write("                        return 1\n")
                f.write("    return 0\n")

            result = detect_complexity(test_file)
            assert result['max_complexity'] > 5  # Complex function detected

    def test_layer_3_security_assertions(self):
        """Layer 3: Verify security assertions with tools."""
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "app.py")
            with open(test_file, 'w') as f:
                f.write("API_KEY = 'sk_test_1234567890abcdef'\n")
                f.write("def query(user_id):\n")
                f.write("    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")\n")

            # INFO_EXPOSURE / DATA_FLOW: trace from input to SQL sink
            flows = trace_data_flow(tmpdir, "user_id", "execute")
            # Should find the flow (user_id variable not directly named, but
            # the pattern should match via f-string presence in SQL method)

            # Security scan finds secrets + SQL injection
            secrets = scan_secrets(test_file)
            sql = scan_sql_injection(test_file)

            assert len(secrets) >= 1
            assert any(s['subtype'] == 'api_key' for s in secrets)
            assert len(sql) >= 1
            assert any(s['type'] == 'sql_injection' for s in sql)

    def test_layer_3_architecture_assertions(self):
        """Layer 3: Verify architecture dependencies."""
        with _TempDir() as tmpdir:
            a_file = os.path.join(tmpdir, "Controller.py")
            with open(a_file, 'w') as f:
                f.write("import Service\n")
            s_file = os.path.join(tmpdir, "Service.py")
            with open(s_file, 'w') as f:
                f.write("# service logic\n")

            # Correct arrow: Controller -> Service
            result = verify_dependency_direction(tmpdir, "Controller", "Service")
            assert result['arrow_correct'] is True

            # Forbidden dependency
            violations = verify_forbidden_dependency(
                tmpdir, [("Controller", "Repository")]
            )
            assert len(violations) == 0  # No Repository imported


# ───────────────────────────────────────────────
# Test 2: Closed-Loop Ticket Lifecycle
# ───────────────────────────────────────────────

class TestClosedLoopLifecycle:
    """Verify Review Ticket state machine end-to-end."""

    def setup_method(self):
        # Clean ticket dir before each test
        if os.path.exists(TICKET_DIR):
            for f in os.listdir(TICKET_DIR):
                if f.endswith('.json'):
                    os.remove(os.path.join(TICKET_DIR, f))

    def test_full_lifecycle_open_to_verified(self):
        """open -> pending -> verified"""
        tid = create_ticket(
            target_agent="yangjian",
            target_file="src/app.py",
            assertion_type="NULL_PATH",
            severity="Critical",
            description="Missing null check",
            evidence={"file": "src/app.py", "line": 42},
            fix_suggestion="Add null check",
        )

        # Verify initial state
        ticket = get_ticket(tid)
        assert ticket['status'] == 'open'
        assert len(ticket['status_history']) == 1

        # Agent submits fix
        update_ticket_status(tid, "pending", actor="yangjian", fixed_file="src/app.py")
        ticket = get_ticket(tid)
        assert ticket['status'] == 'pending'
        assert ticket['fixed_file'] == "src/app.py"

        # WangLingguan verifies
        update_ticket_status(
            tid, "verified", actor="wanglingguan",
            verification_result={"passed": True, "checks": ["null_handling"]}
        )
        ticket = get_ticket(tid)
        assert ticket['status'] == 'verified'
        assert ticket['verified_by'] == "wanglingguan"
        assert ticket['verification_result']['passed'] is True

    def test_lifecycle_with_rejection(self):
        """open -> pending -> reopened -> verified"""
        tid = create_ticket(
            target_agent="taibai",
            target_file="docs/spec.md",
            assertion_type="INFO_EXPOSURE",
            severity="High",
            description="Sensitive data in error",
            evidence={},
            fix_suggestion="Remove internal URLs",
        )

        update_ticket_status(tid, "pending", actor="taibai")
        update_ticket_status(
            tid, "reopened", actor="wanglingguan",
            verification_result={"passed": False, "reason": "still exposes token"}
        )
        ticket = get_ticket(tid)
        assert ticket['status'] == 'reopened'

        # Second attempt
        update_ticket_status(tid, "pending", actor="taibai")
        update_ticket_status(
            tid, "verified", actor="wanglingguan",
            verification_result={"passed": True}
        )
        assert get_ticket(tid)['status'] == 'verified'

    def test_ticket_summary_with_mixed_states(self):
        """Aggregate stats across multiple tickets."""
        t1 = create_ticket(
            target_agent="a", target_file="f1.py",
            assertion_type="NULL_PATH", severity="Critical",
            description="d1", evidence={}, fix_suggestion="f1",
        )
        t2 = create_ticket(
            target_agent="b", target_file="f2.py",
            assertion_type="DATA_FLOW", severity="High",
            description="d2", evidence={}, fix_suggestion="f2",
        )
        t3 = create_ticket(
            target_agent="c", target_file="f3.py",
            assertion_type="CONFIG_SAFE", severity="Warning",
            description="d3", evidence={}, fix_suggestion="f3",
        )

        update_ticket_status(t1, "verified")
        update_ticket_status(t2, "pending")
        # t3 stays open

        summary = get_ticket_summary()
        assert summary['total'] == 3
        assert summary['by_status'].get('verified', 0) == 1
        assert summary['by_status'].get('pending', 0) == 1
        assert summary['by_status'].get('open', 0) == 1
        assert summary['by_severity'].get('Critical', 0) == 1
        assert summary['by_severity'].get('High', 0) == 1
        assert summary['by_severity'].get('Warning', 0) == 1
        assert len(summary['open_tickets']) == 1


# ───────────────────────────────────────────────
# Test 3: Multi-Language Mixed Project
# ───────────────────────────────────────────────

class TestMultiLanguageProject:
    """Analyze a project with multiple languages."""

    def test_mixed_language_call_graph(self):
        """Find callers across Python, PHP, JS, and Go files."""
        with _TempDir() as tmpdir:
            # Python caller
            with open(os.path.join(tmpdir, "app.py"), 'w') as f:
                f.write("def target(): pass\n")
                f.write("def main(): target()\n")

            # PHP caller
            with open(os.path.join(tmpdir, "App.php"), 'w') as f:
                f.write("<?php\n")
                f.write("class App {\n")
                f.write("    public function run() {\n")
                f.write("        $this->target();\n")
                f.write("    }\n")
                f.write("}\n")

            # JS caller
            with open(os.path.join(tmpdir, "app.js"), 'w') as f:
                f.write("function target() {}\n")
                f.write("function main() { target(); }\n")

            # Go caller
            with open(os.path.join(tmpdir, "main.go"), 'w') as f:
                f.write("package main\n")
                f.write("func target() {}\n")
                f.write("func main() { target() }\n")

            result = analyze_call_graph(tmpdir, "target")
            # Python: 1, PHP: 1, JS: 1, Go: 1 = 4 total
            # Note: PHP reports via 'name' extraction
            assert result['call_sites_found'] >= 4, (
                f"Expected >= 4 call sites, got {result['call_sites_found']}: "
                f"{[s['context'] for s in result['call_sites']]}")

            # Verify each language was detected
            contexts = [s['context'] for s in result['call_sites']]
            assert any('target()' in c for c in contexts)

    def test_mixed_language_dependencies(self):
        """Extract imports from multiple languages."""
        with _TempDir() as tmpdir:
            # Python imports
            with open(os.path.join(tmpdir, "main.py"), 'w') as f:
                f.write("import os\n")
                f.write("from datetime import datetime\n")

            # PHP imports
            with open(os.path.join(tmpdir, "Main.php"), 'w') as f:
                f.write("<?php\n")
                f.write("use App\\Models\\User;\n")

            # JS imports
            with open(os.path.join(tmpdir, "main.js"), 'w') as f:
                f.write("import React from 'react';\n")

            # Go imports
            with open(os.path.join(tmpdir, "main.go"), 'w') as f:
                f.write("package main\n")
                f.write('import "fmt"\n')

            py_deps = extract_dependencies(os.path.join(tmpdir, "main.py"))
            php_deps = extract_dependencies(os.path.join(tmpdir, "Main.php"))
            js_deps = extract_dependencies(os.path.join(tmpdir, "main.js"))
            go_deps = extract_dependencies(os.path.join(tmpdir, "main.go"))

            assert len(py_deps) == 2
            assert len(php_deps) == 1
            assert len(js_deps) >= 1
            assert len(go_deps) == 1


# ───────────────────────────────────────────────
# Test 4: AST Fallback Chain
# ───────────────────────────────────────────────

class TestASTFallbackChain:
    """Verify code_caller_tracer fallback behavior."""

    def test_python_uses_ast_in_auto_mode(self):
        """Python projects should use AST analysis in auto mode."""
        with _TempDir() as tmpdir:
            with open(os.path.join(tmpdir, "module.py"), 'w') as f:
                f.write("def target():\n    pass\n")
                f.write("def main():\n")
                f.write("    target()\n")

            result = find_callers(tmpdir, "module", "target", mode="auto")
            assert len(result) == 1

    def test_php_uses_regex_in_auto_mode(self):
        """PHP projects should fall back to regex in auto mode."""
        with _TempDir() as tmpdir:
            with open(os.path.join(tmpdir, "App.php"), 'w') as f:
                f.write("<?php\n")
                f.write("class App {\n")
                f.write("    public function run() {\n")
                f.write("        $app = new App();\n")
                f.write("        $app->target();\n")
                f.write("    }\n")
                f.write("}\n")

            result = find_callers(tmpdir, "App", "target", mode="auto")
            assert len(result) == 1

    def test_ast_only_skips_non_python(self):
        """AST-only mode should return empty for non-Python files."""
        with _TempDir() as tmpdir:
            with open(os.path.join(tmpdir, "app.js"), 'w') as f:
                f.write("function target() {}\n")
                f.write("target();\n")

            result = find_callers(tmpdir, "app", "target", mode="ast")
            assert len(result) == 0


# ───────────────────────────────────────────────
# Test 5: Security Scanner Comprehensive
# ───────────────────────────────────────────────

class TestSecurityScannerComprehensive:
    """Verify security scanner across all vulnerability types."""

    def test_all_scan_types_combined(self):
        """A file with multiple issues should be fully detected."""
        with _TempDir() as tmpdir:
            test_file = os.path.join(tmpdir, "vulnerable.py")
            with open(test_file, 'w') as f:
                f.write("API_KEY = 'sk_test_1234567890abcdef'\n")  # secret
                f.write("DEBUG = True\n")  # misconfig
                f.write("def query(uid):\n")
                f.write("    cursor.execute(f\"SELECT * FROM users WHERE id={uid}\")\n")  # sql injection
                f.write("    eval(uid)\n")  # dangerous eval

            secrets = scan_secrets(test_file)
            sql = scan_sql_injection(test_file)
            misconfig = scan_misconfiguration(test_file)
            dangerous = scan_dangerous_operations(
                "rm -rf /tmp\neval(user_input)\nchmod 777 /var"
            )

            assert len(secrets) >= 1
            assert len(sql) >= 1
            assert len(misconfig) >= 1
            assert len(dangerous) >= 3

    def test_false_positive_control(self):
        """Safe code should produce minimal or no findings."""
        with _TempDir() as tmpdir:
            safe_file = os.path.join(tmpdir, "safe.py")
            with open(safe_file, 'w') as f:
                f.write("def add(a, b):\n")
                f.write("    return a + b\n")
                f.write("DEBUG = False\n")
                f.write("result = add(1, 2)\n")

            secrets = scan_secrets(safe_file)
            sql = scan_sql_injection(safe_file)
            misconfig = scan_misconfiguration(safe_file)

            assert len(secrets) == 0
            assert len(sql) == 0
            assert len(misconfig) == 0


# ───────────────────────────────────────────────
# Test 6: Format Auditor Enhanced
# ───────────────────────────────────────────────

class TestFormatAuditorEnhanced:
    """Verify upgraded format auditor capabilities."""

    def test_yaml_schema_with_date_field(self):
        """YAML frontmatter with date field should pass schema validation."""
        content = "---\ntitle: Test\ndate: 2024-01-15\nstatus: published\n---\nBody"
        result = validate_yaml_schema(content)
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_yaml_schema_invalid_enum(self):
        """Invalid status enum should fail schema validation."""
        content = "---\ntitle: Test\ndate: 2024-01-15\nstatus: bad_status\n---\nBody"
        result = validate_yaml_schema(content)
        assert result['valid'] is False

    def test_markdown_links_internal_anchor(self):
        """Internal anchor links should be validated against headings."""
        content = "[Go to Section](#section-2)\n\n# Section 1\n\n# Section 2"
        broken = check_markdown_links(content)
        assert len(broken) == 0

    def test_markdown_links_broken_anchor(self):
        """Broken anchor links should be reported."""
        content = "[Go to Missing](#missing-section)\n\n# Section 1"
        broken = check_markdown_links(content)
        assert len(broken) == 1
        assert "Anchor" in broken[0]['reason']
