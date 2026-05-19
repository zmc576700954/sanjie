import pytest

from mcp.shared.exceptions import McpError
from skills.tool_yindan.scripts.precise_fix import precise_replace


class TestPreciseFix:
    def test_successful_replace(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")
        result = precise_replace(str(test_file), "hello", "goodbye")
        assert "Success" in result
        assert test_file.read_text(encoding="utf-8") == "goodbye world\n"

    def test_string_not_found(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")
        result = precise_replace(str(test_file), "missing", "goodbye")
        assert "Error: Target string not found" in result

    def test_file_not_found(self):
        result = precise_replace("/nonexistent/file.py", "a", "b")
        assert "Error: File" in result

    def test_syntax_rollback(self, tmp_path):
        test_file = tmp_path / "test.py"
        original = "x = 1\n"
        test_file.write_text(original, encoding="utf-8")
        result = precise_replace(str(test_file), "x = 1", "x = def invalid syntax")
        assert "Syntax check failed" in result
        assert test_file.read_text(encoding="utf-8") == original

    def test_path_traversal_blocked(self, tmp_path):
        with pytest.raises(McpError):
            precise_replace("../../etc/passwd", "a", "b", workspace_root=str(tmp_path))
