"""Tests for Claude format templates and rendering.

Verifies that:
- Templates are loaded correctly from the claude format directory.
- SKILL.md template renders with all expected variables.
- SKILL.md output has proper structure (frontmatter, sections).
- plugin_config.json renders to valid JSON.
- Slash command template renders correctly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from migration.generators.claude_generator import ClaudeFormatGenerator

FORMATS_DIR = Path(__file__).parent.parent.parent / "formats"


# ── Concrete test component ───────────────────────────────────────────────────


class _TestSkill:
    """Minimal skill-like object for template-level tests.

    These tests focus on template loading and rendering, not on the full
    component interface, so we use a lightweight stub.
    """

    pass


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def claude_template_dir() -> Path:
    """Return the Claude format template directory."""
    return FORMATS_DIR / "claude"


@pytest.fixture
def generator(claude_template_dir: Path) -> ClaudeFormatGenerator:
    """Return a ClaudeFormatGenerator instance."""
    return ClaudeFormatGenerator(claude_template_dir)


@pytest.fixture
def sample_variables() -> Dict[str, Any]:
    """Return sample variables for template rendering."""
    return {
        "name": "test_skill",
        "description": "A test skill for verification",
        "version": "1.0.0",
        "type": "skill",
        "instructions": "Do step 1, then step 2.",
        "checklist": "- [ ] Step 1\n- [ ] Step 2",
        "examples": "**Input:** hello\n**Output:** HELLO",
        "when_to_use": "Use when you need testing",
        "tools": "- **tool_a**: Does A",
        "system_prompt": "",
        "config_schema": "{}",
        "dependencies": "[]",
        "core_dependencies": "[]",
        "mcp_config": "{}",
        "mcp_transport": "stdio",
    }


# ── Template Loading Tests ────────────────────────────────────────────────────


class TestClaudeTemplateLoading:
    """Test that Claude templates are loaded from disk."""

    def test_skill_md_template_loaded(self, generator: ClaudeFormatGenerator) -> None:
        """SKILL.md template should be loaded."""
        assert "SKILL.md" in generator._templates

    def test_plugin_config_template_loaded(self, generator: ClaudeFormatGenerator) -> None:
        """plugin_config.json template should be loaded."""
        assert "plugin_config.json" in generator._templates

    def test_slash_command_template_loaded(self, generator: ClaudeFormatGenerator) -> None:
        """Slash command template should be loaded from subdirectory."""
        assert "slash_commands/template.md" in generator._templates

    def test_skill_md_template_has_frontmatter(self, generator: ClaudeFormatGenerator) -> None:
        """SKILL.md template should contain YAML frontmatter markers."""
        template = generator._templates["SKILL.md"]
        assert "---" in template
        assert "{{name}}" in template
        assert "{{description}}" in template
        assert "{{version}}" in template

    def test_plugin_config_template_has_placeholders(self, generator: ClaudeFormatGenerator) -> None:
        """plugin_config.json template should contain variable placeholders."""
        template = generator._templates["plugin_config.json"]
        assert "{{name}}" in template
        assert "{{mcp_config}}" in template


# ── Template Rendering Tests ──────────────────────────────────────────────────


class TestClaudeTemplateRendering:
    """Test template rendering with sample variables."""

    def test_skill_md_renders_name(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should contain the skill name."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "test_skill" in result

    def test_skill_md_renders_description(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should contain the description."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "A test skill for verification" in result

    def test_skill_md_renders_instructions(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should contain the instructions."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "Do step 1, then step 2." in result

    def test_skill_md_renders_version(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md frontmatter should contain the version."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "1.0.0" in result

    def test_skill_md_no_unreplaced_placeholders(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should not contain any {{...}} placeholders."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "{{" not in result
        assert "}}" not in result

    def test_plugin_config_renders_valid_json(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered plugin_config.json should be valid JSON."""
        plugin_vars = {
            "name": sample_variables["name"],
            "version": sample_variables["version"],
            "description": sample_variables["description"],
            "type": sample_variables["type"],
            "mcp_config": json.dumps({}),
        }
        result = generator._render_template("plugin_config.json", plugin_vars)
        parsed = json.loads(result)
        assert parsed["name"] == "test_skill"
        assert parsed["version"] == "1.0.0"

    def test_slash_command_renders(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered slash command template should contain skill name."""
        result = generator._render_template("slash_commands/template.md", sample_variables)
        assert "test_skill" in result


# ── SKILL.md Structure Tests ──────────────────────────────────────────────────


class TestClaudeSkillMdStructure:
    """Test that rendered SKILL.md has the expected structure."""

    def test_has_frontmatter(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """SKILL.md should have YAML frontmatter (--- delimiters)."""
        result = generator._render_template("SKILL.md", sample_variables)
        parts = result.split("---")
        # Should have at least 3 parts: before first ---, frontmatter, after second ---
        assert len(parts) >= 3

    def test_has_name_heading(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """SKILL.md should have an H1 heading with the skill name."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "# test_skill" in result

    def test_has_when_to_use_section(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """SKILL.md should have a 'When to Use' section."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "## When to Use" in result

    def test_has_instructions_section(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """SKILL.md should have an 'Instructions' section."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "## Instructions" in result

    def test_has_checklist_section(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """SKILL.md should have a 'Checklist' section."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "## Checklist" in result

    def test_has_examples_section(
        self, generator: ClaudeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """SKILL.md should have an 'Examples' section."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "## Examples" in result
