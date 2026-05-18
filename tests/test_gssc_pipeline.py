import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from skills.tool_taibai.scripts.gather import gather_sources


def test_gather_single_file(tmp_path):
    test_file = tmp_path / "test.log"
    test_file.write_text("Error line 1\nError line 2", encoding="utf-8", newline="")
    result = gather_sources([str(test_file)])
    assert len(result["sources"]) == 1
    assert result["sources"][0]["type"] == "file"
    assert result["sources"][0]["size_bytes"] == 25
    assert result["total_size_bytes"] == 25


def test_gather_directory_with_pattern(tmp_path):
    (tmp_path / "a.py").write_text("print(1)", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Hello", encoding="utf-8")
    result = gather_sources([str(tmp_path)], patterns=["*.py"])
    assert len(result["sources"]) == 1
    assert result["sources"][0]["path"].endswith("a.py")
