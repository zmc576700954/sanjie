"""Tests for Cursor format templates and rendering.

Verifies that:
- SKILL.md template loads and renders with cursorVersion in frontmatter.
- cursor_config.json template renders to valid JSON.
- Output structure matches Cursor-specific requirements.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from migration.generators.cursor_generator import CursorFormatGenerator

FORMATS_DIR = Path(__file__).parent.parent.parent / "formats"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cursor_template_dir() -> Path:
    """Return the Cursor format template directory."""
    return FORMATS_DIR / "cursor"


@pytest.fixture
def generator(cursor_template_dir: Path) -> CursorFormatGenerator:
    """Return a CursorFormatGenerator instance."""
    return CursorFormatGenerator(cursor_template_dir)


@pytest.fixture
def sample_variables() -> Dict[str, Any]:
    """Return sample variables for template rendering."""
    return {
        "name": "test_skill",
        "description": "A test skill for Cursor",
        "version": "1.0.0",
        "type": "skill",
        "instructions": "Follow these steps.",
        "checklist": "- [ ] Step 1",
        "examples": "**Input:** x\n**Output:** y",
        "tools": "- **tool_a**: Does A",
        "system_prompt": "",
        "config_schema": "{}",
        "dependencies": "[]",
        "core_dependencies": "[]",
        "mcp_config": "{}",
        "mcp_transport": "stdio",
        "when_to_use": "",
    }


# ── Template Loading Tests ────────────────────────────────────────────────────


class TestCursorTemplateLoading:
    """Test that Cursor templates are loaded from disk."""

    def test_skill_md_template_loaded(self, generator: CursorFormatGenerator) -> None:
        """SKILL.md template should be loaded."""
        assert "SKILL.md" in generator._templates

    def test_cursor_config_template_loaded(self, generator: CursorFormatGenerator) -> None:
        """cursor_config.json template should be loaded."""
        assert "cursor_config.json" in generator._templates


# ── SKILL.md Rendering Tests ──────────────────────────────────────────────────


class TestCursorSkillMdRendering:
    """Test SKILL.md template rendering for Cursor format."""

    def test_renders_name(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should contain the skill name."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "test_skill" in result

    def test_has_cursor_version(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should have cursorVersion in frontmatter."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "cursorVersion" in result
        assert ">=0.40" in result

    def test_has_instructions_section(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should have an Instructions section."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "## Instructions" in result

    def test_has_tools_section(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should have a Tools section (Cursor-specific)."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "## Tools" in result

    def test_has_examples_section(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should have an Examples section."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "## Examples" in result

    def test_no_unreplaced_placeholders(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered SKILL.md should not contain any {{...}} placeholders."""
        result = generator._render_template("SKILL.md", sample_variables)
        assert "{{" not in result
        assert "}}" not in result


# ── Cursor Config Tests ───────────────────────────────────────────────────────


class TestCursorConfigRendering:
    """Test cursor_config.json rendering."""

    def test_config_renders_valid_json(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered cursor_config.json should be valid JSON."""
        config_vars = {
            "name": sample_variables["name"],
            "mcp_config": json.dumps({}),
        }
        result = generator._render_template("cursor_config.json", config_vars)
        parsed = json.loads(result)
        assert "test_skill" in parsed["skills"]
        assert "cursorRules" in parsed

    def test_config_has_cursor_rules(
        self, generator: CursorFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """cursor_config.json should include cursorRules with the skill name."""
        config_vars = {
            "name": sample_variables["name"],
            "mcp_config": json.dumps({}),
        }
        result = generator._render_template("cursor_config.json", config_vars)
        parsed = json.loads(result)
        assert "test_skill" in parsed["cursorRules"]["include"]
