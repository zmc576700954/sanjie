"""Full end-to-end workflow tests.

Tests the complete pipeline: create -> implement -> generate -> validate ->
export, plus CLI integration tests using Click's CliRunner.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from click.testing import CliRunner

from cli.main import main
from core.shared.base import ComponentMetadata, ComponentType, CoreComponent
from core.shared.utils import load_manifest, save_manifest
from migration.exporter import ComponentExporter


@pytest.fixture
def project_with_skill(tmp_path: Path) -> Path:
    """Create a complete project with a working skill component.

    Returns the project root directory.
    """
    project_root = tmp_path
    components_dir = project_root / "components"
    component_dir = components_dir / "integration_skill"
    core_dir = component_dir / "core"
    formats_dir = component_dir / "formats"
    core_dir.mkdir(parents=True)
    formats_dir.mkdir(parents=True)

    # Create manifest
    manifest = {
        "name": "integration_skill",
        "type": "skill",
        "version": "1.0.0",
        "description": "Integration test skill",
        "author": "test",
        "created": "2025-06-25",
        "updated": "2025-06-25",
        "tags": ["integration", "test"],
        "core_dependencies": [],
        "supported_tools": ["claude", "zcode", "mcp"],
        "config_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to process",
                }
            },
            "required": ["message"],
        },
        "mcp_config": {
            "transport": "stdio",
            "tools": ["integration_skill_run"],
        },
    }
    save_manifest(component_dir / "manifest.json", manifest)

    # Create core/__init__.py
    (core_dir / "__init__.py").write_text(
        '"""integration_skill -- core implementation."""\n', encoding="utf-8"
    )

    # Create core/integration_skill.py
    skill_code = '''"""integration_skill -- Integration test skill."""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.skills.base import SkillBase


class IntegrationSkill(SkillBase):
    """Integration test skill."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="integration_skill",
            type=ComponentType.SKILL,
            version="1.0.0",
            description="Integration test skill",
            tags=["integration", "test"],
            supported_tools=["claude", "zcode", "mcp"],
        )
        super().__init__(metadata)

    @property
    def instructions(self) -> str:
        return "Process messages for integration testing."

    def get_checklist(self) -> List[str]:
        return ["Read input", "Process message", "Return result"]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        message = input_data.get("message", "")
        return {"result": f"Integrated: {message}"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "message" in input_data
'''
    (core_dir / "integration_skill.py").write_text(skill_code, encoding="utf-8")

    return project_root


class TestFullWorkflow:
    """End-to-end test of the complete workflow."""

    def test_full_pipeline(
        self, project_with_skill: Path, tmp_path: Path
    ) -> None:
        """Test the full create -> generate -> validate -> export pipeline.

        This test:
        1. Loads a created skill component
        2. Generates all supported formats
        3. Validates the generated formats
        4. Exports to a target directory
        5. Verifies exported files exist and are valid
        """
        component_dir = project_with_skill / "components" / "integration_skill"
        manifest = load_manifest(component_dir / "manifest.json")

        # Step 1: Load component
        from cli.generate_cmd import _load_component

        project_root_str = str(project_with_skill)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        try:
            component = _load_component(component_dir, manifest)
        finally:
            if project_root_str in sys.path:
                sys.path.remove(project_root_str)

        assert component.name == "integration_skill"
        assert component.component_type == ComponentType.SKILL

        # Step 2: Generate all formats
        exporter = ComponentExporter.create_default()
        supported_tools = manifest["supported_tools"]
        results = exporter.export(component, manifest, supported_tools, component_dir)

        # Verify all tools were processed
        for tool in supported_tools:
            assert tool in results, f"Tool {tool} not in results"

        # Step 3: Validate generated formats
        from cli.validate_cmd import _read_generated_formats

        for tool in supported_tools:
            generated = _read_generated_formats(component_dir, tool)
            assert len(generated) > 0, f"No files generated for {tool}"

            if tool in exporter.validators:
                result = exporter.validators[tool].validate(generated, manifest)
                # Some validators may have warnings but no errors
                assert result.valid, f"Validation failed for {tool}: {result.errors}"

        # Step 4: Export to a separate directory
        export_dir = tmp_path / "final_export"
        export_dir.mkdir()
        export_results = exporter.export(
            component, manifest, ["claude", "zcode"], export_dir
        )

        # Step 5: Verify exported files
        assert export_results["claude"].valid
        assert export_results["zcode"].valid

        claude_skill_md = export_dir / "formats" / "claude" / "SKILL.md"
        assert claude_skill_md.exists()
        content = claude_skill_md.read_text(encoding="utf-8")
        assert "integration_skill" in content

        zcode_command_md = export_dir / "formats" / "zcode" / "Command.md"
        assert zcode_command_md.exists()
        content = zcode_command_md.read_text(encoding="utf-8")
        assert "integration_skill" in content

    def test_component_execution(self, project_with_skill: Path) -> None:
        """Test that the component's core logic can be executed."""
        component_dir = project_with_skill / "components" / "integration_skill"
        manifest = load_manifest(component_dir / "manifest.json")

        from cli.generate_cmd import _load_component

        project_root_str = str(project_with_skill)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        try:
            component = _load_component(component_dir, manifest)
        finally:
            if project_root_str in sys.path:
                sys.path.remove(project_root_str)

        # Execute the component
        result = component.execute({"message": "hello"})
        assert "result" in result
        assert "Integrated: hello" in result["result"]

        # Validate input
        assert component.validate_input({"message": "test"})
        assert not component.validate_input({})

        # Test instructions property
        assert "integration" in component.instructions.lower() or "process" in component.instructions.lower()

        # Test checklist
        checklist = component.get_checklist()
        assert len(checklist) > 0


class TestCLICommands:
    """Test CLI commands using Click's CliRunner."""

    def test_main_help(self) -> None:
        """Test that the main CLI shows help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "agents-dev" in result.output
        assert "create" in result.output
        assert "generate" in result.output
        assert "export" in result.output
        assert "validate" in result.output
        assert "list" in result.output

    def test_version_option(self) -> None:
        """Test that --version shows the version."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_create_help(self) -> None:
        """Test that the create command shows help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["create", "--help"])
        assert result.exit_code == 0
        assert "COMPONENT_TYPE" in result.output
        assert "NAME" in result.output

    def test_generate_help(self) -> None:
        """Test that the generate command shows help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["generate", "--help"])
        assert result.exit_code == 0
        assert "NAME" in result.output

    def test_export_help(self) -> None:
        """Test that the export command shows help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["export", "--help"])
        assert result.exit_code == 0
        assert "NAME" in result.output
        assert "--output" in result.output

    def test_validate_help(self) -> None:
        """Test that the validate command shows help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "NAME" in result.output

    def test_list_help(self) -> None:
        """Test that the list command shows help text."""
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--help"])
        assert result.exit_code == 0

    def test_create_skill_via_cli(self, tmp_path: Path, monkeypatch) -> None:
        """Test creating a skill component via the CLI."""
        # Change to temp directory so the component is created there
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["create", "skill", "cli_test_skill", "--description", "CLI test skill"],
        )
        assert result.exit_code == 0
        assert "Created component" in result.output

        # Verify directory structure
        component_dir = tmp_path / "components" / "cli_test_skill"
        assert component_dir.exists()
        assert (component_dir / "manifest.json").exists()
        assert (component_dir / "core" / "__init__.py").exists()
        assert (component_dir / "core" / "cli_test_skill.py").exists()
        assert (component_dir / "formats").exists()

        # Verify manifest content
        manifest = load_manifest(component_dir / "manifest.json")
        assert manifest["name"] == "cli_test_skill"
        assert manifest["type"] == "skill"
        assert manifest["description"] == "CLI test skill"

        # Verify skeleton code
        core_file = component_dir / "core" / "cli_test_skill.py"
        content = core_file.read_text(encoding="utf-8")
        assert "class CliTestSkill(SkillBase)" in content
        assert "instructions" in content

    def test_create_agent_via_cli(self, tmp_path: Path, monkeypatch) -> None:
        """Test creating an agent component via the CLI."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["create", "agent", "cli_test_agent", "--description", "CLI test agent"],
        )
        assert result.exit_code == 0

        component_dir = tmp_path / "components" / "cli_test_agent"
        assert component_dir.exists()

        core_file = component_dir / "core" / "cli_test_agent.py"
        content = core_file.read_text(encoding="utf-8")
        assert "class CliTestAgent(AgentBase)" in content
        assert "system_prompt" in content

    def test_create_tool_via_cli(self, tmp_path: Path, monkeypatch) -> None:
        """Test creating a tool component via the CLI."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["create", "tool", "cli_test_tool", "--description", "CLI test tool"],
        )
        assert result.exit_code == 0

        component_dir = tmp_path / "components" / "cli_test_tool"
        assert component_dir.exists()

        core_file = component_dir / "core" / "cli_test_tool.py"
        content = core_file.read_text(encoding="utf-8")
        assert "class CliTestTool(ToolBase)" in content
        assert "function_definitions" in content

    def test_create_duplicate_component_fails(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Test that creating a duplicate component fails."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()

        # Create first component
        result = runner.invoke(
            main, ["create", "skill", "dup_skill"]
        )
        assert result.exit_code == 0

        # Try to create the same component again
        result = runner.invoke(
            main, ["create", "skill", "dup_skill"]
        )
        assert result.exit_code == 1

    def test_list_command_no_components(self, tmp_path: Path, monkeypatch) -> None:
        """Test list command when no components exist."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "No components found" in result.output

    def test_list_command_with_components(
        self, project_with_skill: Path, monkeypatch
    ) -> None:
        """Test list command when components exist."""
        monkeypatch.chdir(project_with_skill)

        runner = CliRunner()
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "integration_skill" in result.output

    def test_list_command_filter_by_type(
        self, project_with_skill: Path, monkeypatch
    ) -> None:
        """Test list command with type filter."""
        monkeypatch.chdir(project_with_skill)

        runner = CliRunner()
        result = runner.invoke(main, ["list", "skill"])
        assert result.exit_code == 0
        assert "integration_skill" in result.output

    def test_list_command_filter_no_match(
        self, project_with_skill: Path, monkeypatch
    ) -> None:
        """Test list command with type filter that matches nothing."""
        monkeypatch.chdir(project_with_skill)

        runner = CliRunner()
        result = runner.invoke(main, ["list", "agent"])
        assert result.exit_code == 0
        assert "No agent components found" in result.output

    def test_validate_nonexistent_component(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Test validating a non-existent component."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["validate", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "Error" in result.output

    def test_generate_nonexistent_component(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Test generating formats for a non-existent component."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["generate", "nonexistent"])
        assert result.exit_code == 1

    def test_create_with_custom_tools_and_tags(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Test creating a component with custom tools and tags."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "create",
                "skill",
                "custom_skill",
                "--tools", "claude,mcp",
                "--tags", "custom,special",
                "--description", "A custom skill",
            ],
        )
        assert result.exit_code == 0

        manifest = load_manifest(
            tmp_path / "components" / "custom_skill" / "manifest.json"
        )
        assert manifest["supported_tools"] == ["claude", "mcp"]
        assert manifest["tags"] == ["custom", "special"]
        assert manifest["description"] == "A custom skill"
