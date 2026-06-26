"""Tests for MCP format templates and rendering.

Verifies that:
- mcp_server.py template loads and renders correctly.
- mcp_config.json template renders to valid JSON.
- MCP server output has proper structure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from migration.generators.mcp_generator import MCPFormatGenerator

FORMATS_DIR = Path(__file__).parent.parent.parent / "formats"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mcp_template_dir() -> Path:
    """Return the MCP format template directory."""
    return FORMATS_DIR / "mcp"


@pytest.fixture
def generator(mcp_template_dir: Path) -> MCPFormatGenerator:
    """Return an MCPFormatGenerator instance."""
    return MCPFormatGenerator(mcp_template_dir)


@pytest.fixture
def sample_variables() -> Dict[str, Any]:
    """Return sample variables for template rendering."""
    return {
        "name": "test_server",
        "description": "A test MCP server",
        "version": "1.0.0",
        "type": "tool",
        "instructions": "",
        "checklist": "",
        "examples": "",
        "tools": "",
        "system_prompt": "",
        "config_schema": "{}",
        "dependencies": "[]",
        "core_dependencies": "[]",
        "mcp_config": "{}",
        "mcp_transport": "stdio",
        "tool_definitions": "@server.tool()\nasync def test_func(**kwargs):\n    pass",
        "tool_handlers": "@server.list_tools()\nasync def list_tools():\n    return []",
        "when_to_use": "",
    }


# ── Template Loading Tests ────────────────────────────────────────────────────


class TestMCPTemplateLoading:
    """Test that MCP templates are loaded from disk."""

    def test_mcp_server_template_loaded(self, generator: MCPFormatGenerator) -> None:
        """mcp_server.py template should be loaded."""
        assert "mcp_server.py" in generator._templates

    def test_mcp_config_template_loaded(self, generator: MCPFormatGenerator) -> None:
        """mcp_config.json template should be loaded."""
        assert "mcp_config.json" in generator._templates


# ── MCP Server Rendering Tests ────────────────────────────────────────────────


class TestMCPServerRendering:
    """Test mcp_server.py template rendering."""

    def test_renders_server_name(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered mcp_server.py should contain the server name."""
        result = generator._render_template("mcp_server.py", sample_variables)
        assert "test_server" in result

    def test_has_imports(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered mcp_server.py should have MCP SDK imports."""
        result = generator._render_template("mcp_server.py", sample_variables)
        assert "from mcp.server import Server" in result

    def test_has_main_function(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered mcp_server.py should have an async main function."""
        result = generator._render_template("mcp_server.py", sample_variables)
        assert "async def main" in result

    def test_has_tool_definitions(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered mcp_server.py should include tool definitions."""
        result = generator._render_template("mcp_server.py", sample_variables)
        assert "test_func" in result

    def test_no_unreplaced_placeholders(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered mcp_server.py should not contain any {{...}} placeholders."""
        result = generator._render_template("mcp_server.py", sample_variables)
        assert "{{" not in result
        assert "}}" not in result


# ── MCP Config Tests ──────────────────────────────────────────────────────────


class TestMCPConfigRendering:
    """Test mcp_config.json rendering."""

    def test_config_renders_valid_json(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """Rendered mcp_config.json should be valid JSON."""
        config_vars = {
            "name": sample_variables["name"],
            "mcp_transport": "stdio",
        }
        result = generator._render_template("mcp_config.json", config_vars)
        parsed = json.loads(result)
        assert "mcpServers" in parsed
        assert "test_server" in parsed["mcpServers"]

    def test_config_has_transport(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """mcp_config.json should include the transport type."""
        config_vars = {
            "name": sample_variables["name"],
            "mcp_transport": "stdio",
        }
        result = generator._render_template("mcp_config.json", config_vars)
        parsed = json.loads(result)
        assert parsed["mcpServers"]["test_server"]["transport"] == "stdio"

    def test_config_has_command(
        self, generator: MCPFormatGenerator, sample_variables: Dict[str, Any]
    ) -> None:
        """mcp_config.json should include the command to start the server."""
        config_vars = {
            "name": sample_variables["name"],
            "mcp_transport": "stdio",
        }
        result = generator._render_template("mcp_config.json", config_vars)
        parsed = json.loads(result)
        assert parsed["mcpServers"]["test_server"]["command"] == "python"
