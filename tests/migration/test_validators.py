"""Tests for all format validators.

Verifies that each validator:
- Accepts valid generated files as valid.
- Reports errors for missing required files.
- Reports errors for invalid content (bad JSON, missing sections, etc.).
- Reports warnings for missing optional sections.
- Uses base class helpers correctly (_check_required_files, _check_non_empty).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

from migration.validators.base import FormatValidator, ValidationResult
from migration.validators.claude_validator import ClaudeFormatValidator
from migration.validators.zcode_validator import ZCodeFormatValidator
from migration.validators.cursor_validator import CursorFormatValidator
from migration.validators.mcp_validator import MCPFormatValidator


# ── ValidationResult Tests ─────────────────────────────────────────────────────


class TestValidationResult:
    """Test ValidationResult dataclass behavior."""

    def test_valid_result_default_lists(self) -> None:
        """A valid result should have empty error and warning lists."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_result_with_errors(self) -> None:
        """An invalid result should list its errors."""
        result = ValidationResult(
            valid=False,
            errors=["Missing file: SKILL.md"],
        )
        assert result.valid is False
        assert len(result.errors) == 1
        assert "Missing file" in result.errors[0]

    def test_result_with_warnings_still_valid(self) -> None:
        """Warnings alone should not make the result invalid."""
        result = ValidationResult(
            valid=True,
            warnings=["Missing Examples section"],
        )
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_result_with_errors_and_warnings(self) -> None:
        """A result can have both errors and warnings."""
        result = ValidationResult(
            valid=False,
            errors=["Missing file: SKILL.md"],
            warnings=["Missing Examples section"],
        )
        assert result.valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1


# ── Base Validator Helper Tests ────────────────────────────────────────────────


class _StubValidator(FormatValidator):
    """A minimal concrete validator to test base class helpers."""

    tool_name = "stub"

    def validate(
        self,
        generated_files: Dict[str, str],
        manifest: Dict[str, Any],
    ) -> ValidationResult:
        return ValidationResult(valid=True)


class TestBaseValidatorHelpers:
    """Test _check_required_files and _check_non_empty helpers."""

    def test_check_required_files_all_present(self) -> None:
        """No errors when all required files are present."""
        validator = _StubValidator()
        files = {"SKILL.md": "content", "plugin_config.json": "{}"}
        errors = validator._check_required_files(files, ["SKILL.md", "plugin_config.json"])
        assert errors == []

    def test_check_required_files_missing(self) -> None:
        """Errors reported for each missing required file."""
        validator = _StubValidator()
        files = {"SKILL.md": "content"}
        errors = validator._check_required_files(files, ["SKILL.md", "plugin_config.json"])
        assert len(errors) == 1
        assert "plugin_config.json" in errors[0]

    def test_check_required_files_all_missing(self) -> None:
        """Errors reported for all missing files."""
        validator = _StubValidator()
        files: Dict[str, str] = {}
        errors = validator._check_required_files(files, ["SKILL.md", "plugin_config.json"])
        assert len(errors) == 2

    def test_check_non_empty_with_content(self) -> None:
        """No errors when file has content."""
        validator = _StubValidator()
        files = {"SKILL.md": "some content"}
        errors = validator._check_non_empty(files, "SKILL.md")
        assert errors == []

    def test_check_non_empty_with_empty_string(self) -> None:
        """Error when file content is empty string."""
        validator = _StubValidator()
        files = {"SKILL.md": ""}
        errors = validator._check_non_empty(files, "SKILL.md")
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_check_non_empty_with_whitespace_only(self) -> None:
        """Error when file content is only whitespace."""
        validator = _StubValidator()
        files = {"SKILL.md": "   \n  \t  "}
        errors = validator._check_non_empty(files, "SKILL.md")
        assert len(errors) == 1

    def test_check_non_empty_missing_file(self) -> None:
        """Error when the file key does not exist in the mapping."""
        validator = _StubValidator()
        files: Dict[str, str] = {}
        errors = validator._check_non_empty(files, "SKILL.md")
        assert len(errors) == 1


# ── ClaudeFormatValidator Tests ────────────────────────────────────────────────


class TestClaudeFormatValidator:
    """Test ClaudeFormatValidator."""

    @pytest.fixture
    def validator(self) -> ClaudeFormatValidator:
        return ClaudeFormatValidator()

    @pytest.fixture
    def valid_skill_md(self) -> str:
        return """---
name: security_scanner
description: Scans code
version: 1.0.0
---

# security_scanner

Scans code

## When to Use
Use when you need to scan code

## Instructions
Scan the code for vulnerabilities.

## Checklist
- [ ] Check SQL injection

## Examples
**Input:** some input
**Output:** some output
"""

    @pytest.fixture
    def valid_plugin_config(self) -> str:
        return json.dumps({
            "name": "security_scanner",
            "version": "1.0.0",
            "description": "Scans code",
            "type": "skill",
        })

    @pytest.fixture
    def sample_manifest(self) -> Dict[str, Any]:
        return {"name": "security_scanner", "type": "skill", "version": "1.0.0"}

    def test_valid_files_pass(
        self,
        validator: ClaudeFormatValidator,
        valid_skill_md: str,
        valid_plugin_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Valid SKILL.md + plugin_config.json should pass validation."""
        files = {"SKILL.md": valid_skill_md, "plugin_config.json": valid_plugin_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is True
        assert result.errors == []

    def test_missing_skill_md(
        self,
        validator: ClaudeFormatValidator,
        valid_plugin_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Missing SKILL.md should produce an error."""
        files = {"plugin_config.json": valid_plugin_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("SKILL.md" in e for e in result.errors)

    def test_missing_plugin_config(
        self,
        validator: ClaudeFormatValidator,
        valid_skill_md: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Missing plugin_config.json should produce an error."""
        files = {"SKILL.md": valid_skill_md}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("plugin_config.json" in e for e in result.errors)

    def test_invalid_json_in_plugin_config(
        self,
        validator: ClaudeFormatValidator,
        valid_skill_md: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Invalid JSON in plugin_config.json should produce an error."""
        files = {
            "SKILL.md": valid_skill_md,
            "plugin_config.json": "{invalid json!!!}",
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("not valid JSON" in e for e in result.errors)

    def test_missing_frontmatter_in_skill_md(
        self,
        validator: ClaudeFormatValidator,
        valid_plugin_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """SKILL.md without YAML frontmatter should produce an error."""
        skill_md = "# security_scanner\n\nSome content\n\n## Instructions\nDo stuff."
        files = {"SKILL.md": skill_md, "plugin_config.json": valid_plugin_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("frontmatter" in e.lower() for e in result.errors)

    def test_missing_name_in_frontmatter(
        self,
        validator: ClaudeFormatValidator,
        valid_plugin_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """SKILL.md with frontmatter missing 'name' should produce an error."""
        skill_md = "---\ndescription: test\nversion: 1.0.0\n---\n\n## Instructions\nDo stuff."
        files = {"SKILL.md": skill_md, "plugin_config.json": valid_plugin_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("name" in e for e in result.errors)

    def test_missing_instructions_section(
        self,
        validator: ClaudeFormatValidator,
        valid_plugin_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """SKILL.md without ## Instructions section should produce an error."""
        skill_md = "---\nname: test\n---\n\n# test\n\nSome content."
        files = {"SKILL.md": skill_md, "plugin_config.json": valid_plugin_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("Instructions" in e for e in result.errors)

    def test_missing_required_fields_in_plugin_config(
        self,
        validator: ClaudeFormatValidator,
        valid_skill_md: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """plugin_config.json missing required fields should produce errors."""
        config = json.dumps({"name": "test"})  # Missing version, description, type
        files = {"SKILL.md": valid_skill_md, "plugin_config.json": config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        # Should have errors for missing version, description, type
        error_text = " ".join(result.errors)
        assert "version" in error_text
        assert "description" in error_text
        assert "type" in error_text

    def test_warnings_for_missing_optional_sections(
        self,
        validator: ClaudeFormatValidator,
        valid_plugin_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """SKILL.md without Examples and Checklist should produce warnings."""
        skill_md = "---\nname: test\n---\n\n## Instructions\nDo stuff."
        files = {"SKILL.md": skill_md, "plugin_config.json": valid_plugin_config}
        result = validator.validate(files, sample_manifest)
        # Should have warnings for missing Examples and Checklist
        assert len(result.warnings) >= 1
        warning_text = " ".join(result.warnings)
        assert "Examples" in warning_text or "Checklist" in warning_text

    def test_unclosed_frontmatter(
        self,
        validator: ClaudeFormatValidator,
        valid_plugin_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """SKILL.md with unclosed frontmatter should produce an error."""
        skill_md = "---\nname: test\n\n## Instructions\nDo stuff."
        files = {"SKILL.md": skill_md, "plugin_config.json": valid_plugin_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("frontmatter" in e.lower() for e in result.errors)


# ── ZCodeFormatValidator Tests ─────────────────────────────────────────────────


class TestZCodeFormatValidator:
    """Test ZCodeFormatValidator."""

    @pytest.fixture
    def validator(self) -> ZCodeFormatValidator:
        return ZCodeFormatValidator()

    @pytest.fixture
    def valid_command_md(self) -> str:
        return """# security_scanner

Scans code for security vulnerabilities

## Usage

```
/security_scanner [arguments]
```

## Instructions
Scan the code for vulnerabilities.

## Checklist
- [ ] Check SQL injection

## Examples
**Input:** some input
**Output:** some output
"""

    @pytest.fixture
    def valid_command_config(self) -> str:
        return json.dumps({
            "name": "security_scanner",
            "description": "Scans code for security vulnerabilities",
            "type": "command",
        })

    @pytest.fixture
    def sample_manifest(self) -> Dict[str, Any]:
        return {"name": "security_scanner", "type": "skill", "version": "1.0.0"}

    def test_valid_files_pass(
        self,
        validator: ZCodeFormatValidator,
        valid_command_md: str,
        valid_command_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Valid Command.md + command_config should pass validation."""
        files = {
            "Command.md": valid_command_md,
            "command_config/template.json": valid_command_config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is True
        assert result.errors == []

    def test_missing_heading(
        self,
        validator: ZCodeFormatValidator,
        valid_command_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Command.md without # heading matching component name should error."""
        command_md = "## Usage\n\n```\n/security_scanner\n```\n\n## Instructions\nDo stuff."
        files = {
            "Command.md": command_md,
            "command_config/template.json": valid_command_config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("heading" in e.lower() for e in result.errors)

    def test_wrong_heading_name(
        self,
        validator: ZCodeFormatValidator,
        valid_command_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Command.md with # heading not matching component name should error."""
        command_md = "# wrong_name\n\n## Usage\n\n```\n/wrong_name\n```\n\n## Instructions\nDo stuff."
        files = {
            "Command.md": command_md,
            "command_config/template.json": valid_command_config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("security_scanner" in e for e in result.errors)

    def test_missing_usage_section(
        self,
        validator: ZCodeFormatValidator,
        valid_command_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Command.md without ## Usage section should error."""
        command_md = "# security_scanner\n\n## Instructions\nDo stuff."
        files = {
            "Command.md": command_md,
            "command_config/template.json": valid_command_config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("Usage" in e for e in result.errors)

    def test_invalid_json_in_config(
        self,
        validator: ZCodeFormatValidator,
        valid_command_md: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Invalid JSON in command_config should produce an error."""
        files = {
            "Command.md": valid_command_md,
            "command_config/template.json": "{bad json!!}",
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("not valid JSON" in e for e in result.errors)

    def test_missing_required_fields_in_config(
        self,
        validator: ZCodeFormatValidator,
        valid_command_md: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """command_config missing name or description should error."""
        config = json.dumps({"type": "command"})  # Missing name and description
        files = {
            "Command.md": valid_command_md,
            "command_config/template.json": config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        error_text = " ".join(result.errors)
        assert "name" in error_text
        assert "description" in error_text

    def test_warning_for_missing_examples(
        self,
        validator: ZCodeFormatValidator,
        valid_command_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Command.md without ## Examples should produce a warning."""
        command_md = "# security_scanner\n\n## Usage\n\n```\n/security_scanner\n```\n\n## Instructions\nDo stuff."
        files = {
            "Command.md": command_md,
            "command_config/template.json": valid_command_config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is True
        assert any("Examples" in w for w in result.warnings)

    def test_missing_command_md(
        self,
        validator: ZCodeFormatValidator,
        valid_command_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Missing Command.md should produce an error."""
        files = {"command_config/template.json": valid_command_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("Command.md" in e for e in result.errors)


# ── CursorFormatValidator Tests ────────────────────────────────────────────────


class TestCursorFormatValidator:
    """Test CursorFormatValidator."""

    @pytest.fixture
    def validator(self) -> CursorFormatValidator:
        return CursorFormatValidator()

    @pytest.fixture
    def valid_skill_md_with_cursor_version(self) -> str:
        return """---
name: security_scanner
description: Scans code
version: 1.0.0
cursorVersion: ">=0.40"
---

# security_scanner

Scans code

## Instructions
Scan the code for vulnerabilities.
"""

    @pytest.fixture
    def valid_skill_md_without_cursor_version(self) -> str:
        return """---
name: security_scanner
description: Scans code
version: 1.0.0
---

# security_scanner

Scans code

## Instructions
Scan the code for vulnerabilities.
"""

    @pytest.fixture
    def valid_cursor_config(self) -> str:
        return json.dumps({
            "skills": ["security_scanner"],
            "mcpServers": {},
            "cursorRules": {"include": ["security_scanner"]},
        })

    @pytest.fixture
    def sample_manifest(self) -> Dict[str, Any]:
        return {"name": "security_scanner", "type": "skill", "version": "1.0.0"}

    def test_valid_files_with_cursor_version(
        self,
        validator: CursorFormatValidator,
        valid_skill_md_with_cursor_version: str,
        valid_cursor_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Valid SKILL.md with cursorVersion should pass validation."""
        files = {
            "SKILL.md": valid_skill_md_with_cursor_version,
            "cursor_config.json": valid_cursor_config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is True
        assert result.errors == []

    def test_missing_cursor_version_produces_warning(
        self,
        validator: CursorFormatValidator,
        valid_skill_md_without_cursor_version: str,
        valid_cursor_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """SKILL.md without cursorVersion should produce a warning but still be valid."""
        files = {
            "SKILL.md": valid_skill_md_without_cursor_version,
            "cursor_config.json": valid_cursor_config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is True
        assert any("cursorVersion" in w for w in result.warnings)

    def test_missing_frontmatter(
        self,
        validator: CursorFormatValidator,
        valid_cursor_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """SKILL.md without YAML frontmatter should produce an error."""
        skill_md = "# security_scanner\n\n## Instructions\nDo stuff."
        files = {"SKILL.md": skill_md, "cursor_config.json": valid_cursor_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("frontmatter" in e.lower() for e in result.errors)

    def test_invalid_cursor_config_json(
        self,
        validator: CursorFormatValidator,
        valid_skill_md_with_cursor_version: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Invalid JSON in cursor_config.json should produce an error."""
        files = {
            "SKILL.md": valid_skill_md_with_cursor_version,
            "cursor_config.json": "{invalid!!}",
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("not valid JSON" in e for e in result.errors)

    def test_missing_skills_in_cursor_config(
        self,
        validator: CursorFormatValidator,
        valid_skill_md_with_cursor_version: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """cursor_config.json without 'skills' field should produce an error."""
        config = json.dumps({"mcpServers": {}})
        files = {
            "SKILL.md": valid_skill_md_with_cursor_version,
            "cursor_config.json": config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("skills" in e for e in result.errors)

    def test_missing_mcp_servers_in_cursor_config(
        self,
        validator: CursorFormatValidator,
        valid_skill_md_with_cursor_version: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """cursor_config.json without 'mcpServers' field should produce an error."""
        config = json.dumps({"skills": ["security_scanner"]})
        files = {
            "SKILL.md": valid_skill_md_with_cursor_version,
            "cursor_config.json": config,
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("mcpServers" in e for e in result.errors)

    def test_missing_skill_md(
        self,
        validator: CursorFormatValidator,
        valid_cursor_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Missing SKILL.md should produce an error."""
        files = {"cursor_config.json": valid_cursor_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("SKILL.md" in e for e in result.errors)


# ── MCPFormatValidator Tests ───────────────────────────────────────────────────


class TestMCPFormatValidator:
    """Test MCPFormatValidator."""

    @pytest.fixture
    def validator(self) -> MCPFormatValidator:
        return MCPFormatValidator()

    @pytest.fixture
    def valid_server_py(self) -> str:
        return '''#!/usr/bin/env python3
"""MCP Server: security_tool - Security scanning tool"""

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("security_tool")

@server.tool()
async def scan_code(**kwargs):
    """Scans code for security vulnerabilities"""
    return {"status": "not_implemented", "function": "scan_code"}

@server.list_tools()
async def list_tools():
    """List all available tools."""
    return []

async def main():
    async with server.run() as runner:
        await runner.wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
'''

    @pytest.fixture
    def valid_mcp_config(self) -> str:
        return json.dumps({
            "mcpServers": {
                "security_tool": {
                    "command": "python",
                    "args": ["path/to/security_tool_server.py"],
                    "transport": "stdio",
                },
            },
        })

    @pytest.fixture
    def sample_manifest(self) -> Dict[str, Any]:
        return {
            "name": "security_tool",
            "type": "tool",
            "version": "1.0.0",
            "mcp_config": {
                "transport": "stdio",
                "tools": ["scan_code"],
            },
        }

    def test_valid_files_pass(
        self,
        validator: MCPFormatValidator,
        valid_server_py: str,
        valid_mcp_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Valid mcp_server.py + mcp_config.json should pass validation."""
        files = {"mcp_server.py": valid_server_py, "mcp_config.json": valid_mcp_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is True
        assert result.errors == []

    def test_invalid_python_syntax(
        self,
        validator: MCPFormatValidator,
        valid_mcp_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """mcp_server.py with invalid Python syntax should produce an error."""
        bad_python = "def foo(\n  # Missing closing paren\n"
        files = {"mcp_server.py": bad_python, "mcp_config.json": valid_mcp_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("syntax" in e.lower() for e in result.errors)

    def test_missing_server_import(
        self,
        validator: MCPFormatValidator,
        valid_mcp_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """mcp_server.py without Server import should produce an error."""
        server_py = '''#!/usr/bin/env python3
"""MCP Server without import"""

server = Server("test")

async def main():
    pass
'''
        files = {"mcp_server.py": server_py, "mcp_config.json": valid_mcp_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("Server import" in e for e in result.errors)

    def test_missing_server_instantiation(
        self,
        validator: MCPFormatValidator,
        valid_mcp_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """mcp_server.py without Server() call should produce an error."""
        server_py = '''#!/usr/bin/env python3
"""MCP Server without instantiation"""

from mcp.server import Server
from mcp.types import Tool, TextContent

async def main():
    pass
'''
        files = {"mcp_server.py": server_py, "mcp_config.json": valid_mcp_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("Server instantiation" in e for e in result.errors)

    def test_invalid_mcp_config_json(
        self,
        validator: MCPFormatValidator,
        valid_server_py: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Invalid JSON in mcp_config.json should produce an error."""
        files = {
            "mcp_server.py": valid_server_py,
            "mcp_config.json": "{bad json!!}",
        }
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("not valid JSON" in e for e in result.errors)

    def test_missing_mcp_servers_in_config(
        self,
        validator: MCPFormatValidator,
        valid_server_py: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """mcp_config.json without mcpServers should produce an error."""
        config = json.dumps({"name": "test"})
        files = {"mcp_server.py": valid_server_py, "mcp_config.json": config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("mcpServers" in e for e in result.errors)

    def test_empty_mcp_servers(
        self,
        validator: MCPFormatValidator,
        valid_server_py: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """mcp_config.json with empty mcpServers should produce an error."""
        config = json.dumps({"mcpServers": {}})
        files = {"mcp_server.py": valid_server_py, "mcp_config.json": config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_server_entry_missing_command(
        self,
        validator: MCPFormatValidator,
        valid_server_py: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """mcp_config.json server entry without command field should error."""
        config = json.dumps({
            "mcpServers": {
                "security_tool": {
                    "args": ["path/to/server.py"],
                },
            },
        })
        files = {"mcp_server.py": valid_server_py, "mcp_config.json": config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("command" in e for e in result.errors)

    def test_warning_for_missing_async_main(
        self,
        validator: MCPFormatValidator,
        valid_mcp_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """mcp_server.py without async def main should produce a warning."""
        server_py = '''#!/usr/bin/env python3
"""MCP Server without main"""

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("test")

@server.tool()
async def scan_code(**kwargs):
    """Scans code"""
    return {}
'''
        files = {"mcp_server.py": server_py, "mcp_config.json": valid_mcp_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is True
        assert any("main" in w for w in result.warnings)

    def test_missing_server_py(
        self,
        validator: MCPFormatValidator,
        valid_mcp_config: str,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """Missing mcp_server.py should produce an error."""
        files = {"mcp_config.json": valid_mcp_config}
        result = validator.validate(files, sample_manifest)
        assert result.valid is False
        assert any("mcp_server.py" in e for e in result.errors)
