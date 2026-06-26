"""Tests for ZCode format templates and rendering.

Verifies that:
- Command.md template loads and renders correctly.
- Command.md output has expected sections (Usage, Instructions, Checklist, Examples).
- command_config.json template renders to valid JSON with proper argument mapping.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from migration.generators.zcode_generator import ZCodeFormatGenerator

FORMATS_DIR = Path(__file__).parent.parent.parent / "formats"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def zcode_template_dir() -> Path:
    """Return the ZCode format template directory."""
    return FORMATS_DIR / "zcode"


@pytest.fixture
def generator(zcode_template_dir: Path) -> ZCodeFormatGenerator:
    """Return a ZCodeFormatGenerator instance."""
    return ZCodeFormatGenerator(zcode_template_dir)


@pytest.fixture
def sample_variables() -> Dict[str, Any]:
    """Return sample variables for template rendering."""
    return {
        "name": "test_command",
        "description": "A test command for ZCode",
        "version": "1.0.0",
        "type": "skill",
        "instructions": "Run step 1, then step 2.",
        "checklist": "- [ ] Step 1\n- [ ] Step 2",
        "examples": "**Input:** hello\n**Output:** HELLO",
        "tools": "",
        "system_prompt": "",
        "config_schema": json.dumps({"properties": {"input": {"type": "string"}}, "required": ["input"]}),
        "dependencies": "[]",
        "core_dependencies": "[]",
        "mcp_config": "{}",
        "mcp_transport": "stdio",
        "when_to_use": "",
    }


# ── Template Loading Tests ────────────────────────────────────────────────────


class TestZCodeTemplateLoading:
    """Test that ZCode templates are loaded from disk."""

    def test_command_md_template_loaded(self, generator: ZCodeFormatGenerator) -> None:
        """Command.md template should be loaded."""
        assert "Command.md" in generator._templates

    def test_command_config_template_loaded(self, generator: ZCodeFormatGenerator) -> None:
        """command_config/template.json should be loaded."""
        assert "command_config/template.json" in generator._templates


# ── Command.md Rendering Tests ────────────────────────────────────────────────


class TestZCodeCommandMdRendering:
    """Test Command.md template rendering."""

    def test_renders_name(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered Command.md should contain the command name."""
        result = generator._render_template("Command.md", sample_variables)
        assert "test_command" in result

    def test_renders_description(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered Command.md should contain the description."""
        result = generator._render_template("Command.md", sample_variables)
        assert "A test command for ZCode" in result

    def test_has_usage_section(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Command.md should have a Usage section."""
        result = generator._render_template("Command.md", sample_variables)
        assert "## Usage" in result

    def test_has_instructions_section(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Command.md should have an Instructions section."""
        result = generator._render_template("Command.md", sample_variables)
        assert "## Instructions" in result

    def test_has_checklist_section(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Command.md should have a Checklist section."""
        result = generator._render_template("Command.md", sample_variables)
        assert "## Checklist" in result

    def test_has_examples_section(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Command.md should have an Examples section."""
        result = generator._render_template("Command.md", sample_variables)
        assert "## Examples" in result

    def test_no_unreplaced_placeholders(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered Command.md should not contain any {{...}} placeholders."""
        result = generator._render_template("Command.md", sample_variables)
        assert "{{" not in result
        assert "}}" not in result


# ── Command Config Tests ──────────────────────────────────────────────────────


class TestZCodeCommandConfig:
    """Test command_config.json rendering."""

    def test_config_renders_valid_json(
        self, generator: ZCodeFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered command_config.json should be valid JSON."""
        config_vars = {
            "name": sample_variables["name"],
            "description": sample_variables["description"],
            "config_schema": json.dumps({}),
            "core_dependencies": json.dumps([]),
        }
        result = generator._render_template("command_config/template.json", config_vars)
        parsed = json.loads(result)
        assert parsed["name"] == "test_command"
        assert parsed["type"] == "command"

    def test_config_map_arguments(self) -> None:
        """_map_config_to_arguments should map JSON Schema to command arguments."""
        config_schema = {
            "properties": {
                "input_text": {"type": "string", "description": "The input text"},
                "count": {"type": "integer", "description": "Number of items"},
            },
            "required": ["input_text"],
        }
        result = ZCodeFormatGenerator._map_config_to_arguments(config_schema)
        assert "input_text" in result
        assert result["input_text"]["required"] is True
        assert result["input_text"]["type"] == "string"
        assert "count" in result
        assert result["count"]["required"] is False
