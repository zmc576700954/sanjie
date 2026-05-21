import os
import tempfile

from skills.tool_wanglingguan.scripts.format_auditor import (
    audit_content,
    validate_yaml_schema,
    check_markdown_links,
)


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
        content = '```json A2A_ENVELOPE\n{"target_agent": "nezha"}\n```'
        result = audit_content(content, "handoff")
        assert result["status"] == "PASS"

    def test_handoff_missing_block(self):
        content = "No handoff block"
        result = audit_content(content, "handoff")
        assert result["status"] == "FAIL"
        assert "Missing" in result["errors"][0]

    def test_handoff_invalid_json(self):
        content = '```json A2A_ENVELOPE\n{invalid json}\n```'
        result = audit_content(content, "handoff")
        assert result["status"] == "FAIL"
        assert "Invalid JSON" in result["errors"][0]

    def test_unknown_check_type(self):
        result = audit_content("anything", "unknown")
        assert result["status"] == "FAIL"


class TestValidateYamlSchema:
    def test_schema_pass(self):
        content = "---\ntitle: Test\ndate: 2024-01-01\nstatus: draft\n---\nBody"
        result = validate_yaml_schema(content)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_schema_fail_missing_key(self):
        content = "---\ntitle: Test\ndate: 2024-01-01\n---\nBody"
        result = validate_yaml_schema(content)
        assert result["valid"] is False
        assert any("required" in err.lower() for err in result["errors"])

    def test_schema_fail_invalid_status(self):
        content = "---\ntitle: Test\ndate: 2024-01-01\nstatus: invalid_status\n---\nBody"
        result = validate_yaml_schema(content)
        assert result["valid"] is False

    def test_schema_no_frontmatter(self):
        content = "No frontmatter here"
        result = validate_yaml_schema(content)
        assert result["valid"] is False
        assert any("Missing YAML frontmatter" in err for err in result["errors"])

    def test_custom_schema(self):
        content = "---\nname: Test\nversion: 1.0\n---\nBody"
        schema = {
            "type": "object",
            "required": ["name", "version"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
            },
        }
        result = validate_yaml_schema(content, schema)
        assert result["valid"] is True


class TestCheckMarkdownLinks:
    def test_valid_links(self):
        content = "[Link](./file.md)\n[Anchor](#section-1)\n\n# Section 1"
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "file.md")
            with open(test_file, 'w') as f:
                f.write("# File\n")
            result = check_markdown_links(content, base_path=tmpdir)
            assert len(result) == 0

    def test_broken_file_link(self):
        content = "[Missing](./nonexistent.md)"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_markdown_links(content, base_path=tmpdir)
            assert len(result) == 1
            assert "File not found" in result[0]["reason"]

    def test_broken_anchor_link(self):
        content = "[Missing](#nonexistent-section)\n\n# Existing Section"
        result = check_markdown_links(content)
        assert len(result) == 1
        assert "Anchor" in result[0]["reason"]

    def test_external_link_skipped(self):
        content = "[External](https://example.com)"
        result = check_markdown_links(content)
        assert len(result) == 0

    def test_image_link_skipped(self):
        content = "![Alt](./image.png)"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_markdown_links(content, base_path=tmpdir)
            assert len(result) == 0
