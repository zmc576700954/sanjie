from skills.tool_wanglingguan.scripts.format_auditor import audit_content


class TestFormatAuditor:
    def test_document_pass(self):
        content = "---\ntitle: Test\ndate: 2024-01-01\nstatus: draft\n---\nBody"
        result = audit_content(content, "document")
        assert result["status"] == "PASS"

    def test_document_missing_frontmatter(self):
        content = "No frontmatter here"
        result = audit_content(content, "document")
        assert result["status"] == "FAIL"
        assert any("Missing or malformed YAML Frontmatter" in err for err in result["errors"])

    def test_document_missing_keys(self):
        content = "---\ntitle: Test\n---\nBody"
        result = audit_content(content, "document")
        assert result["status"] == "FAIL"

    def test_handoff_pass(self):
        content = '```json A2A_HANDOFF\n{"target_agent": "nezha"}\n```'
        result = audit_content(content, "handoff")
        assert result["status"] == "PASS"

    def test_handoff_missing_block(self):
        content = "No handoff block"
        result = audit_content(content, "handoff")
        assert result["status"] == "FAIL"
        assert "Missing" in result["errors"][0]

    def test_handoff_invalid_json(self):
        content = '```json A2A_HANDOFF\n{invalid json}\n```'
        result = audit_content(content, "handoff")
        assert result["status"] == "FAIL"
        assert "Invalid JSON" in result["errors"][0]

    def test_unknown_check_type(self):
        result = audit_content("anything", "unknown")
        assert result["status"] == "FAIL"
