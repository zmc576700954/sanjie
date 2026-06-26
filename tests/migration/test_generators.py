"""Tests for all format generators.

Verifies that each generator:
- Works with a sample SkillBase component.
- Works with a sample ToolBase component.
- Extracts variables correctly.
- Renders templates correctly.
- Returns the expected output file structure (correct keys in returned dict).
- Generates content that contains expected sections.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from core.shared.base import ComponentMetadata, ComponentType
from core.agents.base import AgentBase
from core.skills.base import SkillBase
from core.tools.base import ToolBase
from migration.generators.base import FormatGenerator
from migration.generators.claude_generator import ClaudeFormatGenerator
from migration.generators.zcode_generator import ZCodeFormatGenerator
from migration.generators.cursor_generator import CursorFormatGenerator
from migration.generators.reasionix_generator import ReasionixFormatGenerator
from migration.generators.mcp_generator import MCPFormatGenerator

FORMATS_DIR = Path(__file__).parent.parent.parent / "formats"


# ── Concrete test components ──────────────────────────────────────────────────


class SampleSkill(SkillBase):
    """A concrete SkillBase for generator tests."""

    @property
    def instructions(self) -> str:
        return "Scan the code for vulnerabilities.\n1. Check SQL injection.\n2. Check XSS."

    def get_checklist(self) -> List[str]:
        return ["Check SQL injection", "Check XSS vulnerabilities", "Check hardcoded secrets"]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "scanned"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "code" in input_data


class SampleAgent(AgentBase):
    """A concrete AgentBase for generator tests."""

    @property
    def system_prompt(self) -> str:
        return "You are a security analysis agent."

    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        return [{"name": "scan_tool", "description": "Scans code for issues"}]

    def plan(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"action": "scan", "task": task}]

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"needs_adjustment": False}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "task" in input_data


class SampleTool(ToolBase):
    """A concrete ToolBase for generator tests."""

    @property
    def function_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "scan_code",
                "description": "Scans code for security vulnerabilities",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "The code to scan"},
                        "language": {"type": "string", "description": "Programming language"},
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "get_report",
                "description": "Gets a formatted report of findings",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "description": "Report format"},
                    },
                },
            },
        ]

    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        if function_name == "scan_code":
            return {"findings": []}
        if function_name == "get_report":
            return {"report": "No issues found"}
        return None

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "function" in input_data


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_skill() -> SampleSkill:
    """Return a SampleSkill instance with examples."""
    metadata = ComponentMetadata(
        name="security_scanner",
        type=ComponentType.SKILL,
        version="1.2.0",
        description="Scans code for security vulnerabilities",
        tags=["security", "scanning"],
        core_dependencies=["pathlib", "re"],
        config_schema={"required": ["code"], "properties": {"code": {"type": "string"}}},
    )
    skill = SampleSkill(metadata)
    skill._examples = [
        {"input": "SELECT * FROM users WHERE id = " + "'1'", "output": "SQL injection found"},
        {"input": "<div>{{user_input}}</div>", "output": "XSS vulnerability found"},
    ]
    return skill


@pytest.fixture
def sample_agent() -> SampleAgent:
    """Return a SampleAgent instance."""
    metadata = ComponentMetadata(
        name="security_agent",
        type=ComponentType.AGENT,
        version="2.0.0",
        description="Security analysis agent",
    )
    return SampleAgent(metadata)


@pytest.fixture
def sample_tool() -> SampleTool:
    """Return a SampleTool instance."""
    metadata = ComponentMetadata(
        name="security_tool",
        type=ComponentType.TOOL,
        version="1.0.0",
        description="Security scanning tool",
        core_dependencies=["pathlib"],
    )
    return SampleTool(metadata)


@pytest.fixture
def sample_manifest() -> Dict[str, Any]:
    """Return a sample manifest.json content."""
    return {
        "name": "security_scanner",
        "type": "skill",
        "version": "1.2.0",
        "description": "Scans code for security vulnerabilities",
        "core_dependencies": ["pathlib", "re"],
        "config_schema": {
            "required": ["code"],
            "properties": {
                "code": {"type": "string", "description": "The code to scan"},
                "language": {"type": "string", "description": "Programming language"},
            },
        },
        "mcp_config": {
            "transport": "stdio",
            "tools": ["scan_code", "get_report"],
        },
        "when_to_use": "Use when you need to scan code for security issues",
    }


@pytest.fixture
def claude_generator() -> ClaudeFormatGenerator:
    """Return a ClaudeFormatGenerator instance."""
    return ClaudeFormatGenerator(FORMATS_DIR / "claude")


@pytest.fixture
def zcode_generator() -> ZCodeFormatGenerator:
    """Return a ZCodeFormatGenerator instance."""
    return ZCodeFormatGenerator(FORMATS_DIR / "zcode")


@pytest.fixture
def cursor_generator() -> CursorFormatGenerator:
    """Return a CursorFormatGenerator instance."""
    return CursorFormatGenerator(FORMATS_DIR / "cursor")


@pytest.fixture
def reasionix_generator() -> ReasionixFormatGenerator:
    """Return a ReasionixFormatGenerator instance."""
    return ReasionixFormatGenerator(FORMATS_DIR / "reasionix")


@pytest.fixture
def mcp_generator() -> MCPFormatGenerator:
    """Return an MCPFormatGenerator instance."""
    return MCPFormatGenerator(FORMATS_DIR / "mcp")


# ── Variable Extraction Tests ─────────────────────────────────────────────────


class TestVariableExtraction:
    """Test that _extract_variables works correctly for each component type."""

    def test_skill_variable_extraction(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """SkillBase should extract instructions, checklist, and examples."""
        variables = claude_generator._extract_variables(sample_skill, sample_manifest)
        assert variables["name"] == "security_scanner"
        assert variables["type"] == "skill"
        assert variables["version"] == "1.2.0"
        assert "SQL injection" in variables["instructions"]
        assert "- [ ] Check SQL injection" in variables["checklist"]
        assert "SQL injection found" in variables["examples"]

    def test_agent_variable_extraction(
        self, claude_generator: ClaudeFormatGenerator, sample_agent: SampleAgent, sample_manifest: Dict[str, Any]
    ) -> None:
        """AgentBase should extract system_prompt and tools."""
        variables = claude_generator._extract_variables(sample_agent, sample_manifest)
        assert variables["name"] == "security_agent"
        assert "security analysis agent" in variables["system_prompt"]
        assert "scan_tool" in variables["tools"]

    def test_tool_variable_extraction(
        self, claude_generator: ClaudeFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """ToolBase should extract function_definitions as tools."""
        variables = claude_generator._extract_variables(sample_tool, sample_manifest)
        assert variables["name"] == "security_tool"
        assert "scan_code" in variables["tools"]
        assert "get_report" in variables["tools"]

    def test_manifest_fields_extracted(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Manifest fields like mcp_config and when_to_use should be extracted."""
        variables = claude_generator._extract_variables(sample_skill, sample_manifest)
        assert "stdio" in variables["mcp_transport"]
        assert "scan code for security issues" in variables["when_to_use"]


# ── Claude Generator Tests ────────────────────────────────────────────────────


class TestClaudeGenerator:
    """Test ClaudeFormatGenerator with real components."""

    def test_skill_generates_skill_md(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Claude generator should produce SKILL.md for a skill."""
        output = claude_generator.generate(sample_skill, sample_manifest)
        assert "SKILL.md" in output

    def test_skill_generates_plugin_config(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Claude generator should produce plugin_config.json for a skill."""
        output = claude_generator.generate(sample_skill, sample_manifest)
        assert "plugin_config.json" in output

    def test_skill_generates_slash_command(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Claude generator should produce slash command for a skill."""
        output = claude_generator.generate(sample_skill, sample_manifest)
        assert "slash_commands/template.md" in output

    def test_skill_md_has_frontmatter(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated SKILL.md should have YAML frontmatter."""
        output = claude_generator.generate(sample_skill, sample_manifest)
        skill_md = output["SKILL.md"]
        assert "---" in skill_md
        assert "name: security_scanner" in skill_md

    def test_skill_md_has_sections(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated SKILL.md should have all expected sections."""
        output = claude_generator.generate(sample_skill, sample_manifest)
        skill_md = output["SKILL.md"]
        assert "## When to Use" in skill_md
        assert "## Instructions" in skill_md
        assert "## Checklist" in skill_md
        assert "## Examples" in skill_md

    def test_plugin_config_valid_json(
        self, claude_generator: ClaudeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated plugin_config.json should be valid JSON."""
        output = claude_generator.generate(sample_skill, sample_manifest)
        parsed = json.loads(output["plugin_config.json"])
        assert parsed["name"] == "security_scanner"
        assert parsed["type"] == "skill"

    def test_tool_generates_output(
        self, claude_generator: ClaudeFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """Claude generator should produce output for a ToolBase component."""
        output = claude_generator.generate(sample_tool, sample_manifest)
        assert "SKILL.md" in output
        assert "plugin_config.json" in output


# ── ZCode Generator Tests ─────────────────────────────────────────────────────


class TestZCodeGenerator:
    """Test ZCodeFormatGenerator with real components."""

    def test_skill_generates_command_md(
        self, zcode_generator: ZCodeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """ZCode generator should produce Command.md for a skill."""
        output = zcode_generator.generate(sample_skill, sample_manifest)
        assert "Command.md" in output

    def test_skill_generates_command_config(
        self, zcode_generator: ZCodeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """ZCode generator should produce command_config.json for a skill."""
        output = zcode_generator.generate(sample_skill, sample_manifest)
        assert "command_config/template.json" in output

    def test_command_md_has_sections(
        self, zcode_generator: ZCodeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated Command.md should have expected sections."""
        output = zcode_generator.generate(sample_skill, sample_manifest)
        command_md = output["Command.md"]
        assert "## Usage" in command_md
        assert "## Instructions" in command_md
        assert "## Checklist" in command_md
        assert "## Examples" in command_md

    def test_command_md_contains_name(
        self, zcode_generator: ZCodeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated Command.md should contain the skill name."""
        output = zcode_generator.generate(sample_skill, sample_manifest)
        assert "security_scanner" in output["Command.md"]

    def test_command_config_valid_json(
        self, zcode_generator: ZCodeFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated command_config.json should be valid JSON."""
        output = zcode_generator.generate(sample_skill, sample_manifest)
        parsed = json.loads(output["command_config/template.json"])
        assert parsed["name"] == "security_scanner"
        assert parsed["type"] == "command"

    def test_tool_generates_output(
        self, zcode_generator: ZCodeFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """ZCode generator should produce output for a ToolBase component."""
        output = zcode_generator.generate(sample_tool, sample_manifest)
        assert "Command.md" in output


# ── Cursor Generator Tests ────────────────────────────────────────────────────


class TestCursorGenerator:
    """Test CursorFormatGenerator with real components."""

    def test_skill_generates_skill_md(
        self, cursor_generator: CursorFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Cursor generator should produce SKILL.md for a skill."""
        output = cursor_generator.generate(sample_skill, sample_manifest)
        assert "SKILL.md" in output

    def test_skill_generates_cursor_config(
        self, cursor_generator: CursorFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Cursor generator should produce cursor_config.json for a skill."""
        output = cursor_generator.generate(sample_skill, sample_manifest)
        assert "cursor_config.json" in output

    def test_skill_md_has_cursor_version(
        self, cursor_generator: CursorFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated SKILL.md should have cursorVersion in frontmatter."""
        output = cursor_generator.generate(sample_skill, sample_manifest)
        skill_md = output["SKILL.md"]
        assert "cursorVersion" in skill_md

    def test_skill_md_has_tools_section(
        self, cursor_generator: CursorFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated SKILL.md should have a Tools section."""
        output = cursor_generator.generate(sample_skill, sample_manifest)
        skill_md = output["SKILL.md"]
        assert "## Tools" in skill_md

    def test_cursor_config_valid_json(
        self, cursor_generator: CursorFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated cursor_config.json should be valid JSON."""
        output = cursor_generator.generate(sample_skill, sample_manifest)
        parsed = json.loads(output["cursor_config.json"])
        assert "skills" in parsed
        assert "cursorRules" in parsed

    def test_tool_generates_output(
        self, cursor_generator: CursorFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """Cursor generator should produce output for a ToolBase component."""
        output = cursor_generator.generate(sample_tool, sample_manifest)
        assert "SKILL.md" in output
        assert "cursor_config.json" in output


# ── Reasionix Generator Tests ─────────────────────────────────────────────────


class TestReasionixGenerator:
    """Test ReasionixFormatGenerator with real components."""

    def test_skill_generates_script(
        self, reasionix_generator: ReasionixFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Reasionix generator should produce a Python script for a skill."""
        output = reasionix_generator.generate(sample_skill, sample_manifest)
        assert "script_templates/template.py" in output

    def test_skill_generates_deepseek_config(
        self, reasionix_generator: ReasionixFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Reasionix generator should produce deepseek_config.json for a skill."""
        output = reasionix_generator.generate(sample_skill, sample_manifest)
        assert "deepseek_config/template.json" in output

    def test_script_has_shebang(
        self, reasionix_generator: ReasionixFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated script should have a Python shebang line."""
        output = reasionix_generator.generate(sample_skill, sample_manifest)
        script = output["script_templates/template.py"]
        assert script.startswith("#!/usr/bin/env python3")

    def test_script_has_argparse(
        self, reasionix_generator: ReasionixFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated script should include argparse-based CLI."""
        output = reasionix_generator.generate(sample_skill, sample_manifest)
        script = output["script_templates/template.py"]
        assert "argparse" in script

    def test_script_has_instructions_as_comments(
        self, reasionix_generator: ReasionixFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated script should have instructions as Python comments."""
        output = reasionix_generator.generate(sample_skill, sample_manifest)
        script = output["script_templates/template.py"]
        assert "# Scan the code for vulnerabilities." in script

    def test_deepseek_config_valid_json(
        self, reasionix_generator: ReasionixFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated deepseek_config.json should be valid JSON."""
        output = reasionix_generator.generate(sample_skill, sample_manifest)
        parsed = json.loads(output["deepseek_config/template.json"])
        assert parsed["name"] == "security_scanner"
        assert parsed["model"] == "deepseek"
        assert parsed["optimizations"]["chunked_prompts"] is True

    def test_tool_generates_output(
        self, reasionix_generator: ReasionixFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """Reasionix generator should produce output for a ToolBase component."""
        output = reasionix_generator.generate(sample_tool, sample_manifest)
        assert "script_templates/template.py" in output
        assert "deepseek_config/template.json" in output


# ── MCP Generator Tests ───────────────────────────────────────────────────────


class TestMCPGenerator:
    """Test MCPFormatGenerator with real components."""

    def test_tool_generates_server(
        self, mcp_generator: MCPFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """MCP generator should produce mcp_server.py for a tool."""
        output = mcp_generator.generate(sample_tool, sample_manifest)
        assert "mcp_server.py" in output

    def test_tool_generates_config(
        self, mcp_generator: MCPFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """MCP generator should produce mcp_config.json for a tool."""
        output = mcp_generator.generate(sample_tool, sample_manifest)
        assert "mcp_config.json" in output

    def test_server_has_tool_definitions(
        self, mcp_generator: MCPFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated mcp_server.py should include tool function definitions."""
        output = mcp_generator.generate(sample_tool, sample_manifest)
        server = output["mcp_server.py"]
        assert "scan_code" in server
        assert "get_report" in server

    def test_server_has_mcp_imports(
        self, mcp_generator: MCPFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated mcp_server.py should have MCP SDK imports."""
        output = mcp_generator.generate(sample_tool, sample_manifest)
        server = output["mcp_server.py"]
        assert "from mcp.server import Server" in server

    def test_config_valid_json(
        self, mcp_generator: MCPFormatGenerator, sample_tool: SampleTool, sample_manifest: Dict[str, Any]
    ) -> None:
        """Generated mcp_config.json should be valid JSON."""
        output = mcp_generator.generate(sample_tool, sample_manifest)
        parsed = json.loads(output["mcp_config.json"])
        assert "mcpServers" in parsed
        assert "security_tool" in parsed["mcpServers"]

    def test_skill_generates_output(
        self, mcp_generator: MCPFormatGenerator, sample_skill: SampleSkill, sample_manifest: Dict[str, Any]
    ) -> None:
        """MCP generator should produce output for a SkillBase component."""
        output = mcp_generator.generate(sample_skill, sample_manifest)
        assert "mcp_server.py" in output
        assert "mcp_config.json" in output


# ── Cross-Generator Consistency Tests ─────────────────────────────────────────


class TestCrossGeneratorConsistency:
    """Test that all generators produce consistent output for the same component."""

    def test_all_generators_produce_output_for_skill(
        self,
        claude_generator: ClaudeFormatGenerator,
        zcode_generator: ZCodeFormatGenerator,
        cursor_generator: CursorFormatGenerator,
        reasionix_generator: ReasionixFormatGenerator,
        mcp_generator: MCPFormatGenerator,
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """All five generators should produce non-empty output for a skill."""
        generators = [
            claude_generator,
            zcode_generator,
            cursor_generator,
            reasionix_generator,
            mcp_generator,
        ]
        for gen in generators:
            output = gen.generate(sample_skill, sample_manifest)
            assert len(output) > 0, f"{gen.tool_name} generator produced empty output"
            for key, content in output.items():
                assert len(content) > 0, f"{gen.tool_name} produced empty content for {key}"

    def test_all_generators_include_component_name(
        self,
        claude_generator: ClaudeFormatGenerator,
        zcode_generator: ZCodeFormatGenerator,
        cursor_generator: CursorFormatGenerator,
        reasionix_generator: ReasionixFormatGenerator,
        mcp_generator: MCPFormatGenerator,
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """All generators should include the component name in their output."""
        generators = [
            claude_generator,
            zcode_generator,
            cursor_generator,
            reasionix_generator,
            mcp_generator,
        ]
        for gen in generators:
            output = gen.generate(sample_skill, sample_manifest)
            all_content = " ".join(output.values())
            assert "security_scanner" in all_content, (
                f"{gen.tool_name} output does not contain component name"
            )

    def test_all_generators_produce_output_for_tool(
        self,
        claude_generator: ClaudeFormatGenerator,
        zcode_generator: ZCodeFormatGenerator,
        cursor_generator: CursorFormatGenerator,
        reasionix_generator: ReasionixFormatGenerator,
        mcp_generator: MCPFormatGenerator,
        sample_tool: SampleTool,
        sample_manifest: Dict[str, Any],
    ) -> None:
        """All five generators should produce non-empty output for a tool."""
        generators = [
            claude_generator,
            zcode_generator,
            cursor_generator,
            reasionix_generator,
            mcp_generator,
        ]
        for gen in generators:
            output = gen.generate(sample_tool, sample_manifest)
            assert len(output) > 0, f"{gen.tool_name} generator produced empty output for tool"


# ── Template Rendering Edge Cases ─────────────────────────────────────────────


class TestTemplateRenderingEdgeCases:
    """Test edge cases in template rendering."""

    def test_render_with_missing_variables(
        self, claude_generator: ClaudeFormatGenerator
    ) -> None:
        """Missing variables should be replaced with empty string."""
        result = claude_generator._render_template("SKILL.md", {"name": "test"})
        # The template should render without error, unreplaced vars become empty
        assert "test" in result
        assert "{{" not in result

    def test_render_with_empty_variables(
        self, claude_generator: ClaudeFormatGenerator
    ) -> None:
        """Empty variable values should render as empty strings."""
        variables = {
            "name": "test",
            "description": "",
            "version": "",
            "instructions": "",
            "checklist": "",
            "examples": "",
            "when_to_use": "",
        }
        result = claude_generator._render_template("SKILL.md", variables)
        assert "test" in result
        assert "{{" not in result

    def test_render_nonexistent_template_raises(
        self, claude_generator: ClaudeFormatGenerator
    ) -> None:
        """Rendering a non-existent template should raise TemplateError."""
        from core.shared.errors import TemplateError

        with pytest.raises(TemplateError):
            claude_generator._render_template("nonexistent.template", {})

    def test_checklist_formatting(self) -> None:
        """_format_checklist should produce markdown checkbox items."""
        result = FormatGenerator._format_checklist(["Item A", "Item B"])
        assert "- [ ] Item A" in result
        assert "- [ ] Item B" in result

    def test_examples_formatting(self) -> None:
        """_format_examples should produce markdown input/output pairs."""
        examples = [
            {"input": "hello", "output": "HELLO"},
            {"input": "world", "output": "WORLD"},
        ]
        result = FormatGenerator._format_examples(examples)
        assert "**Input:** hello" in result
        assert "**Output:** HELLO" in result
        assert "**Input:** world" in result

    def test_empty_examples_formatting(self) -> None:
        """_format_examples with empty list should return empty string."""
        result = FormatGenerator._format_examples([])
        assert result == ""

    def test_tools_formatting(self) -> None:
        """_format_tools should produce markdown tool list."""
        tools = [
            {"name": "scan", "description": "Scans code"},
            {"name": "report", "description": "Generates report"},
        ]
        result = FormatGenerator._format_tools(tools)
        assert "- **scan**: Scans code" in result
        assert "- **report**: Generates report" in result

    def test_empty_tools_formatting(self) -> None:
        """_format_tools with empty list should return empty string."""
        result = FormatGenerator._format_tools([])
        assert result == ""
