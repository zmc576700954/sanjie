import json
import os
import subprocess
import sys
import tempfile

from skills.tool_wanglingguan.scripts.security_scanner import (
    scan_secrets,
    scan_sql_injection,
    scan_xss_vectors,
    scan_misconfiguration,
    scan_dangerous_operations,
)


class TestScanSecrets:
    def test_api_key_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "config.py")
            with open(test_file, 'w') as f:
                f.write("API_KEY = 'sk_test_1234567890abcdef1234'\n")

            result = scan_secrets(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'api_key' for r in result)

    def test_jwt_secret_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "config.py")
            with open(test_file, 'w') as f:
                f.write("JWT_SECRET = 'my_super_secret_key_12345'\n")

            result = scan_secrets(test_file)
            assert len(result) >= 1

    def test_password_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "config.py")
            with open(test_file, 'w') as f:
                f.write("password = 'hunter2_password_123'\n")

            result = scan_secrets(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'password' for r in result)

    def test_no_false_positive_short_string(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "config.py")
            with open(test_file, 'w') as f:
                f.write("x = 'abc'\n")
                f.write("y = 'hello'\n")

            result = scan_secrets(test_file)
            assert len(result) == 0

    def test_high_entropy_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "config.py")
            with open(test_file, 'w') as f:
                f.write("token = 'aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890'\n")

            result = scan_secrets(test_file)
            assert len(result) >= 1

    def test_file_not_found(self):
        result = scan_secrets("/nonexistent/path.py")
        assert 'error' in result[0]


class TestScanSQLInjection:
    def test_f_string_sql(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "db.py")
            with open(test_file, 'w') as f:
                f.write("def query(user_id):\n")
                f.write("    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")\n")

            result = scan_sql_injection(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'f_string_in_sql' for r in result)

    def test_string_concat_sql(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "db.py")
            with open(test_file, 'w') as f:
                f.write("def query(name):\n")
                f.write("    sql = \"SELECT * FROM users WHERE name = '\" + name + \"'\"\n")
                f.write("    cursor.execute(sql)\n")

            result = scan_sql_injection(test_file)
            assert len(result) >= 1

    def test_safe_parameterized_query(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "db.py")
            with open(test_file, 'w') as f:
                f.write("def query(user_id):\n")
                f.write("    cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))\n")

            result = scan_sql_injection(test_file)
            # Should not flag parameterized queries
            assert len(result) == 0

    def test_ast_string_concat_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "db.py")
            with open(test_file, 'w') as f:
                f.write("def bad_query(table, value):\n")
                f.write("    cursor.execute(\"SELECT * FROM \" + table + \" WHERE x = \" + value)\n")

            result = scan_sql_injection(test_file)
            assert len(result) >= 1
            assert any(r['type'] == 'sql_injection' for r in result)


class TestScanXSSVectors:
    def test_innerhtml_assignment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "app.js")
            with open(test_file, 'w') as f:
                f.write("element.innerHTML = userInput;\n")

            result = scan_xss_vectors(test_file)
            assert len(result) >= 1
            assert result[0]['subtype'] == 'innerHTML_assignment'

    def test_document_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "app.js")
            with open(test_file, 'w') as f:
                f.write("document.write(userContent);\n")

            result = scan_xss_vectors(test_file)
            assert len(result) >= 1
            assert result[0]['subtype'] == 'document_write'

    def test_mark_safe(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "views.py")
            with open(test_file, 'w') as f:
                f.write("from django.utils.safestring import mark_safe\n")
                f.write("html = mark_safe(user_html)\n")

            result = scan_xss_vectors(test_file)
            assert len(result) >= 1
            assert result[0]['subtype'] == 'mark_safe'

    def test_no_xss_safe_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "safe.py")
            with open(test_file, 'w') as f:
                f.write("x = 1 + 2\n")
                f.write("print('hello')\n")

            result = scan_xss_vectors(test_file)
            assert len(result) == 0


class TestScanMisconfiguration:
    def test_debug_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "settings.py")
            with open(test_file, 'w') as f:
                f.write("DEBUG = True\n")

            result = scan_misconfiguration(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'debug_enabled' for r in result)

    def test_weak_password_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "auth.py")
            with open(test_file, 'w') as f:
                f.write("hash = md5(password)\n")

            result = scan_misconfiguration(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'weak_password_hash' for r in result)

    def test_cors_wildcard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "settings.py")
            with open(test_file, 'w') as f:
                f.write("CORS_ALLOWED_ORIGINS = ['*']\n")

            result = scan_misconfiguration(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'cors_wildcard' for r in result)

    def test_eval_usage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "utils.py")
            with open(test_file, 'w') as f:
                f.write("result = eval(expression)\n")

            result = scan_misconfiguration(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'eval_enabled' for r in result)

    def test_pickle_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "cache.py")
            with open(test_file, 'w') as f:
                f.write("data = pickle.load(open('cache.pkl', 'rb'))\n")

            result = scan_misconfiguration(test_file)
            assert len(result) >= 1
            assert any(r['subtype'] == 'pickle_load' for r in result)

    def test_safe_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "settings.py")
            with open(test_file, 'w') as f:
                f.write("DEBUG = False\n")
                f.write("ALLOWED_HOSTS = ['example.com']\n")

            result = scan_misconfiguration(test_file)
            assert len(result) == 0


class TestScanDangerousOperations:
    def test_rm_rf(self):
        content = "rm -rf /important/data"
        result = scan_dangerous_operations(content)
        assert len(result) >= 1
        assert result[0]['subtype'] == 'rm_rf'

    def test_chmod_777(self):
        content = "chmod 777 /var/www"
        result = scan_dangerous_operations(content)
        assert len(result) >= 1
        assert result[0]['subtype'] == 'chmod_777'

    def test_drop_table(self):
        content = "DROP TABLE users CASCADE"
        result = scan_dangerous_operations(content)
        assert len(result) >= 1
        assert result[0]['subtype'] == 'drop_table'

    def test_eval_untrusted(self):
        content = "result = eval(user_input)"
        result = scan_dangerous_operations(content)
        assert len(result) >= 1
        assert result[0]['subtype'] == 'eval_untrusted'

    def test_os_system(self):
        content = "os.system(command)"
        result = scan_dangerous_operations(content)
        assert len(result) >= 1
        assert result[0]['subtype'] == 'os_system'

    def test_no_dangerous_ops(self):
        content = "x = 1 + 2\nprint('hello world')"
        result = scan_dangerous_operations(content)
        assert len(result) == 0

    def test_multiple_operations(self):
        content = """rm -rf /tmp/data
chmod 777 /var/log
DROP TABLE old_logs"""
        result = scan_dangerous_operations(content)
        assert len(result) == 3
        subtypes = {r['subtype'] for r in result}
        assert 'rm_rf' in subtypes
        assert 'chmod_777' in subtypes
        assert 'drop_table' in subtypes


class TestSecurityScannerCLI:
    """Test CLI entry points via subprocess."""

    def _run_cli(self, *args):
        cmd = [sys.executable, "-m", "skills.tool_wanglingguan.scripts.security_scanner", *args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def test_cli_all_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "vulnerable.py")
            with open(test_file, 'w') as f:
                f.write("API_KEY = 'sk_test_1234567890abcdef'\n")
                f.write("DEBUG = True\n")

            result = self._run_cli("all", "--file", test_file)
            assert result.returncode == 0, f"stderr: {result.stderr}"
            data = json.loads(result.stdout)
            assert "secrets" in data
            assert "misconfiguration" in data
            assert len(data["secrets"]) >= 1
            assert len(data["misconfiguration"]) >= 1

    def test_cli_secrets_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "config.py")
            with open(test_file, 'w') as f:
                f.write("API_KEY = 'sk_test_1234567890abcdef'\n")

            result = self._run_cli("secrets", "--file", test_file)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert len(data) >= 1
            assert data[0]["type"] == "hardcoded_secret"

    def test_cli_dangerous_ops_command(self):
        result = self._run_cli("dangerous_ops", "--content", "rm -rf /tmp")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data) >= 1
        assert data[0]["subtype"] == "rm_rf"

    def test_cli_file_not_found(self):
        result = self._run_cli("secrets", "--file", "/nonexistent/path.py")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "error" in data[0]
