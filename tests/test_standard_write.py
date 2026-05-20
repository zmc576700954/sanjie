import pytest

from mcp.shared.exceptions import McpError
from skills.tool_taie.scripts.standard_write import write_with_validation


class TestStandardWrite:
    def test_successful_write(self, tmp_path):
        test_file = tmp_path / "test.py"
        result = write_with_validation(str(test_file), "x = 1\n")
        assert "Success" in result
        assert test_file.read_text(encoding="utf-8") == "x = 1\n"

    def test_syntax_rollback(self, tmp_path):
        test_file = tmp_path / "test.py"
        original = "x = 1\n"
        test_file.write_text(original, encoding="utf-8")
        result = write_with_validation(str(test_file), "x = def invalid\n")
        assert "Error: Regression validation failed" in result
        assert test_file.read_text(encoding="utf-8") == original

    def test_dangerous_call_blocked_direct(self, tmp_path):
        """import os + os.system() should be blocked (dangerous call)."""
        test_file = tmp_path / "test.py"
        result = write_with_validation(
            str(test_file), "import os\nos.system('echo test')\n"
        )
        assert "Error: Regression validation failed" in result
        assert "Dangerous call detected" in result

    def test_dangerous_call_blocked_import_from(self, tmp_path):
        """from os import system + system() should be blocked."""
        test_file = tmp_path / "test.py"
        result = write_with_validation(
            str(test_file), "from os import system\nsystem('echo test')\n"
        )
        assert "Error: Regression validation failed" in result
        assert "Dangerous call detected" in result

    def test_legitimate_import_passes(self, tmp_path):
        """import os without dangerous calls should now PASS."""
        test_file = tmp_path / "test.py"
        result = write_with_validation(
            str(test_file), "import os\nos.path.join('a', 'b')\n"
        )
        assert "Success" in result

    def test_empty_function_blocked(self, tmp_path):
        test_file = tmp_path / "test.py"
        result = write_with_validation(str(test_file), "def foo():\n    pass\n")
        assert "Error: Regression validation failed" in result
        assert "Empty function body" in result

    def test_path_traversal(self, tmp_path):
        with pytest.raises(McpError):
            write_with_validation("../../etc/passwd", "x=1", workspace_root=str(tmp_path))
