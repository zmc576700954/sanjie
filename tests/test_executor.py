import pytest

from mcp.shared.exceptions import McpError
from skills.tool_sanjian.scripts.executor import execute_write


class TestExecutor:
    def test_rewrite_success(self, tmp_path):
        test_file = tmp_path / "test.py"
        result = execute_write(str(test_file), "x = 1\n")
        assert result["success"] is True
        assert test_file.read_text(encoding="utf-8") == "x = 1\n"

    def test_rewrite_with_backup(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("original\n", encoding="utf-8")
        result = execute_write(str(test_file), "x = 1\n", backup=True)
        assert result["success"] is True
        assert result["backup_path"] == str(test_file) + ".sanjian_backup"
        assert (tmp_path / "test.py.sanjian_backup").exists()

    def test_syntax_rollback(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("original\n", encoding="utf-8")
        result = execute_write(str(test_file), "x = def invalid\n", backup=True)
        assert result["success"] is False
        assert test_file.read_text(encoding="utf-8") == "original\n"
        assert not (tmp_path / "test.py.sanjian_backup").exists()

    def test_path_traversal(self, tmp_path):
        with pytest.raises(McpError):
            execute_write("../../etc/passwd", "x=1", workspace_root=str(tmp_path))
