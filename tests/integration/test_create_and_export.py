"""Integration tests for the create -> generate -> validate -> export workflow.

Tests the full pipeline from creating a new component through generating
formats, validating them, and exporting to a target directory.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from core.shared.base import ComponentMetadata, ComponentType
from core.shared.utils import load_manifest, save_manifest
from migration.exporter import ComponentExporter


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with components/ structure."""
    components_dir = tmp_path / "components"
    components_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_skill_component(temp_project: Path) -> Path:
    """Create a sample skill component in the temp project directory.

    Returns the path to the component directory.
    """
    component_dir = temp_project / "components" / "test_skill"
    core_dir = component_dir / "core"
    formats_dir = component_dir / "formats"
    core_dir.mkdir(parents=True)
    formats_dir.mkdir(parents=True)

    # Create manifest
    manifest = {
        "name": "test_skill",
        "type": "skill",
        "version": "1.0.0",
        "description": "A test skill for integration testing",
        "author": "test",
        "created": "2025-06-25",
        "updated": "2025-06-25",
        "tags": ["test"],
        "core_dependencies": [],
        "supported_tools": ["claude", "zcode", "mcp"],
        "config_schema": {},
    }
    save_manifest(component_dir / "manifest.json", manifest)

    # Create core/__init__.py
    (core_dir / "__init__.py").write_text(
        '"""test_skill -- core implementation."""\n', encoding="utf-8"
    )

    # Create core/test_skill.py with a working skill implementation
    skill_code = '''"""test_skill -- A test skill for integration testing."""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.skills.base import SkillBase


class TestSkill(SkillBase):
    """A test skill for integration testing."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="test_skill",
            type=ComponentType.SKILL,
            version="1.0.0",
            description="A test skill for integration testing",
            tags=["test"],
            supported_tools=["claude", "zcode", "mcp"],
        )
        super().__init__(metadata)

    @property
    def instructions(self) -> str:
        return "Test skill instructions for integration testing."

    def get_checklist(self) -> List[str]:
        return ["Step 1: Read input", "Step 2: Process", "Step 3: Return result"]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        message = input_data.get("message", "")
        return {"result": f"Processed: {message}"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True
'''
    (core_dir / "test_skill.py").write_text(skill_code, encoding="utf-8")

    return component_dir


class TestCreateAndGenerate:
    """Test creating a component and generating formats."""

    def test_generate_claude_format(
        self, sample_skill_component: Path, temp_project: Path
    ) -> None:
        """Test generating Claude format for a skill component."""
        manifest = load_manifest(sample_skill_component / "manifest.json")

        # Load the component
        from cli.generate_cmd import _load_component

        # Temporarily add project root to sys.path
        project_root = str(temp_project)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            component = _load_component(sample_skill_component, manifest)
        finally:
            if project_root in sys.path:
                sys.path.remove(project_root)

        # Generate Claude format
        exporter = ComponentExporter.create_default()
        results = exporter.export(component, manifest, ["claude"], sample_skill_component)

        # Verify generation succeeded
        assert "claude" in results
        assert results["claude"].valid

        # Verify files were written
        claude_dir = sample_skill_component / "formats" / "claude"
        assert claude_dir.exists()
        skill_md = claude_dir / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        assert "test_skill" in content

    def test_generate_zcode_format(
        self, sample_skill_component: Path, temp_project: Path
    ) -> None:
        """Test generating ZCode format for a skill component."""
        manifest = load_manifest(sample_skill_component / "manifest.json")

        from cli.generate_cmd import _load_component

        project_root = str(temp_project)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            component = _load_component(sample_skill_component, manifest)
        finally:
            if project_root in sys.path:
                sys.path.remove(project_root)

        exporter = ComponentExporter.create_default()
        results = exporter.export(component, manifest, ["zcode"], sample_skill_component)

        assert "zcode" in results
        assert results["zcode"].valid

        zcode_dir = sample_skill_component / "formats" / "zcode"
        assert zcode_dir.exists()
        command_md = zcode_dir / "Command.md"
        assert command_md.exists()
        content = command_md.read_text(encoding="utf-8")
        assert "test_skill" in content

    def test_generate_mcp_format(
        self, sample_skill_component: Path, temp_project: Path
    ) -> None:
        """Test generating MCP format for a skill component."""
        manifest = load_manifest(sample_skill_component / "manifest.json")

        from cli.generate_cmd import _load_component

        project_root = str(temp_project)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            component = _load_component(sample_skill_component, manifest)
        finally:
            if project_root in sys.path:
                sys.path.remove(project_root)

        exporter = ComponentExporter.create_default()
        results = exporter.export(component, manifest, ["mcp"], sample_skill_component)

        assert "mcp" in results
        # MCP format for a skill (not a tool) may have warnings but should still generate
        mcp_dir = sample_skill_component / "formats" / "mcp"
        assert mcp_dir.exists()


class TestValidate:
    """Test validating generated formats."""

    def test_validate_claude_format(
        self, sample_skill_component: Path, temp_project: Path
    ) -> None:
        """Test validating Claude format after generation."""
        manifest = load_manifest(sample_skill_component / "manifest.json")

        from cli.generate_cmd import _load_component

        project_root = str(temp_project)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            component = _load_component(sample_skill_component, manifest)
        finally:
            if project_root in sys.path:
                sys.path.remove(project_root)

        # Generate first
        exporter = ComponentExporter.create_default()
        exporter.export(component, manifest, ["claude"], sample_skill_component)

        # Now validate
        from cli.validate_cmd import _read_generated_formats

        generated = _read_generated_formats(sample_skill_component, "claude")
        assert len(generated) > 0

        result = exporter.validators["claude"].validate(generated, manifest)
        assert result.valid

    def test_validate_zcode_format(
        self, sample_skill_component: Path, temp_project: Path
    ) -> None:
        """Test validating ZCode format after generation."""
        manifest = load_manifest(sample_skill_component / "manifest.json")

        from cli.generate_cmd import _load_component

        project_root = str(temp_project)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            component = _load_component(sample_skill_component, manifest)
        finally:
            if project_root in sys.path:
                sys.path.remove(project_root)

        exporter = ComponentExporter.create_default()
        exporter.export(component, manifest, ["zcode"], sample_skill_component)

        from cli.validate_cmd import _read_generated_formats

        generated = _read_generated_formats(sample_skill_component, "zcode")
        assert len(generated) > 0

        result = exporter.validators["zcode"].validate(generated, manifest)
        assert result.valid


class TestExport:
    """Test exporting components to target directories."""

    def test_export_to_temp_directory(
        self, sample_skill_component: Path, temp_project: Path, tmp_path: Path
    ) -> None:
        """Test exporting to a separate output directory."""
        manifest = load_manifest(sample_skill_component / "manifest.json")

        from cli.generate_cmd import _load_component

        project_root = str(temp_project)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            component = _load_component(sample_skill_component, manifest)
        finally:
            if project_root in sys.path:
                sys.path.remove(project_root)

        # Export to a separate temp directory
        output_dir = tmp_path / "export_output"
        output_dir.mkdir()

        exporter = ComponentExporter.create_default()
        results = exporter.export(component, manifest, ["claude", "zcode"], output_dir)

        # Verify both tools exported
        assert "claude" in results
        assert "zcode" in results
        assert results["claude"].valid
        assert results["zcode"].valid

        # Verify files exist in output directory
        assert (output_dir / "formats" / "claude" / "SKILL.md").exists()
        assert (output_dir / "formats" / "zcode" / "Command.md").exists()

    def test_export_unsupported_tool(
        self, sample_skill_component: Path, temp_project: Path
    ) -> None:
        """Test that exporting to an unsupported tool reports an error."""
        manifest = load_manifest(sample_skill_component / "manifest.json")

        from cli.generate_cmd import _load_component

        project_root = str(temp_project)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            component = _load_component(sample_skill_component, manifest)
        finally:
            if project_root in sys.path:
                sys.path.remove(project_root)

        exporter = ComponentExporter.create_default()
        results = exporter.export(
            component, manifest, ["nonexistent_tool"], sample_skill_component
        )

        assert "nonexistent_tool" in results
        assert not results["nonexistent_tool"].valid
        assert any("Unsupported" in e for e in results["nonexistent_tool"].errors)


class TestCreateWorkflow:
    """Test the create command workflow."""

    def test_create_skill_scaffold(self, temp_project: Path) -> None:
        """Test that creating a skill produces the correct directory structure."""
        from cli.create_cmd import (
            _build_manifest,
            _render_skeleton,
            SKELETONS,
        )
        from core.shared.base import ComponentType

        name = "my_new_skill"
        ctype = ComponentType.SKILL
        description = "A new test skill"
        tags = ["test"]
        tools = ["claude", "zcode"]

        # Build manifest
        manifest = _build_manifest(name, ctype, description, tools, tags)
        assert manifest["name"] == name
        assert manifest["type"] == "skill"
        assert manifest["description"] == description
        assert manifest["supported_tools"] == tools
        assert manifest["tags"] == tags

        # Render skeleton
        skeleton = SKELETONS[ctype]
        rendered = _render_skeleton(skeleton, name, description, tags, tools)
        assert "class MyNewSkill(SkillBase)" in rendered
        assert 'name="my_new_skill"' in rendered
        assert "A new test skill" in rendered

    def test_create_agent_scaffold(self) -> None:
        """Test that creating an agent produces the correct skeleton."""
        from cli.create_cmd import _build_manifest, _render_skeleton, SKELETONS
        from core.shared.base import ComponentType

        name = "my_agent"
        ctype = ComponentType.AGENT
        description = "A test agent"
        tags = ["agent"]
        tools = ["claude"]

        manifest = _build_manifest(name, ctype, description, tools, tags)
        assert manifest["type"] == "agent"

        skeleton = SKELETONS[ctype]
        rendered = _render_skeleton(skeleton, name, description, tags, tools)
        assert "class MyAgent(AgentBase)" in rendered
        assert "system_prompt" in rendered

    def test_create_tool_scaffold(self) -> None:
        """Test that creating a tool produces the correct skeleton."""
        from cli.create_cmd import _build_manifest, _render_skeleton, SKELETONS
        from core.shared.base import ComponentType

        name = "my_tool"
        ctype = ComponentType.TOOL
        description = "A test tool"
        tags = ["tool"]
        tools = ["mcp"]

        manifest = _build_manifest(name, ctype, description, tools, tags)
        assert manifest["type"] == "tool"

        skeleton = SKELETONS[ctype]
        rendered = _render_skeleton(skeleton, name, description, tags, tools)
        assert "class MyTool(ToolBase)" in rendered
        assert "function_definitions" in rendered

    def test_create_mcp_server_scaffold(self) -> None:
        """Test that creating an MCP server produces the correct skeleton."""
        from cli.create_cmd import _build_manifest, _render_skeleton, SKELETONS
        from core.shared.base import ComponentType

        name = "my_mcp_server"
        ctype = ComponentType.MCP_SERVER
        description = "A test MCP server"
        tags = ["mcp"]
        tools = ["mcp"]

        manifest = _build_manifest(name, ctype, description, tools, tags)
        assert manifest["type"] == "mcp_server"
        assert "mcp_config" in manifest

        skeleton = SKELETONS[ctype]
        rendered = _render_skeleton(skeleton, name, description, tags, tools)
        assert "class MyMcpServerServer(MCPServerBase)" in rendered
        assert "get_server_info" in rendered

    def test_snake_case_conversion(self) -> None:
        """Test that component names are converted to snake_case."""
        from core.shared.utils import snake_case

        assert snake_case("MySkill") == "my_skill"
        assert snake_case("some-name") == "some_name"
        assert snake_case("already_snake") == "already_snake"

    def test_class_name_conversion(self) -> None:
        """Test that snake_case names are converted to CamelCase class names."""
        from cli.create_cmd import _to_class_name

        assert _to_class_name("my_skill") == "MySkill"
        assert _to_class_name("data_analysis") == "DataAnalysis"
        assert _to_class_name("simple") == "Simple"
