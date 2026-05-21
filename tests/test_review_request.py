import json
import os
import pytest
from skills.tool_taibai.scripts.review_request import request_review


class TestRequestReview:
    def test_request_review_format_type(self, tmp_path, monkeypatch):
        doc = tmp_path / "doc.md"
        doc.write_text("# Test\n---\ntitle: T\ndate: 2026-05-21\nstatus: active\n---\nContent", encoding="utf-8")
        monkeypatch.setattr("skills.tool_taibai.scripts.review_request.A2A_INBOX_DIR", str(tmp_path / "a2a_inbox"))
        result = request_review(str(doc), review_type="format")
        assert result["status"] == "submitted"
        assert "ticket_id" in result
        assert result["review_type"] == "format"

    def test_request_review_all_types(self, tmp_path, monkeypatch):
        doc = tmp_path / "doc.md"
        doc.write_text("Content", encoding="utf-8")
        monkeypatch.setattr("skills.tool_taibai.scripts.review_request.A2A_INBOX_DIR", str(tmp_path / "a2a_inbox"))
        for rt in ["format", "quality", "assertion", "architecture"]:
            result = request_review(str(doc), review_type=rt)
            assert result["status"] == "submitted"
            assert result["review_type"] == rt

    def test_request_review_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            request_review(str(tmp_path / "missing.md"))

    def test_request_review_file_written(self, tmp_path, monkeypatch):
        doc = tmp_path / "doc.md"
        doc.write_text("Content", encoding="utf-8")
        inbox = tmp_path / "a2a_inbox"
        monkeypatch.setattr("skills.tool_taibai.scripts.review_request.A2A_INBOX_DIR", str(inbox))
        result = request_review(str(doc), review_type="quality", context_notes="Check facts")
        # Verify review request file was written
        pending_dir = inbox / "pending"
        files = list(pending_dir.glob("*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["to"] == "review-pool"
        assert data["payload"]["review_type"] == "quality"
        assert data["payload"]["context_notes"] == "Check facts"
