import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from skills.tool_taibai.scripts.gather import gather_sources
from skills.tool_taibai.scripts.select import select_content
from skills.tool_taibai.scripts.structure import structure_document


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


def test_select_removes_conversation_filler():
    raw = {
        "sources": [
            {
                "path": "chat.log",
                "type": "file",
                "content_preview": "Let me check that for you.\nI think the issue is here.\nBased on my analysis, the bug is at line 42.",
            }
        ],
        "total_size_bytes": 100,
        "estimated_tokens": 20,
    }
    result = select_content(raw)
    assert "Let me check" not in result["filtered_sources"][0]["content_preview"]
    assert "Based on my analysis" not in result["filtered_sources"][0]["content_preview"]
    assert "line 42" in result["filtered_sources"][0]["content_preview"]
    assert result["removed_stats"]["noise_lines"] >= 2


def test_structure_spec_document():
    selected = {
        "filtered_sources": [
            {"path": "design.md", "content_preview": "We decided to use async."}
        ]
    }
    doc = structure_document(selected, doc_type="spec", author="taibai")
    assert doc.startswith("---")
    assert "title:" in doc
    assert "status: active" in doc
    assert "author: taibai" in doc
    assert "Summary" in doc
    assert "Implementation" in doc
    assert "We decided to use async." in doc
