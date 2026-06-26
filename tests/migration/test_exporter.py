"""Tests for ComponentExporter.

Verifies that the exporter:
- Exports a component to all specified tools.
- Exports a component to a single tool.
- Handles unsupported tools gracefully (records error, continues).
- Writes files to disk correctly.
- Handles partial failure (one tool fails, others succeed).
- create_default() returns a properly configured exporter.
- _write_files creates necessary directories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from core.shared.base import ComponentMetadata, ComponentType
from core.skills.base import SkillBase
from core.tools.base import ToolBase
from core.shared.errors import FormatGenerationError
from migration.generators.base import FormatGenerator
from migration.generators.claude_generator import ClaudeFormatGenerator
from migration.generators.zcode_generator import ZCodeFormatGenerator
from migration.generators.cursor_generator import CursorFormatGenerator
from migration.generators.reasionix_generator import ReasionixFormatGenerator
from migration.generators.mcp_generator import MCPFormatGenerator
from migration.validators.base import FormatValidator, ValidationResult
from migration.validators.claude_validator import ClaudeFormatValidator
from migration.validators.zcode_validator import ZCodeFormatValidator
from migration.validators.cursor_validator import CursorFormatValidator
from migration.validators.mcp_validator import MCPFormatValidator
from migration.exporter import ComponentExporter

FORMATS_DIR = Path(__file__).parent.parent.parent / "formats"


# ── Concrete test components ──────────────────────────────────────────────────


class SampleSkill(SkillBase):
    """A concrete SkillBase for exporter tests."""

    @property
    def instructions(self) -> str:
        return "Scan the code for vulnerabilities.\n1. Check SQL injection.\n2. Check XSS."

    def get_checklist(self) -> List[str]:
        return ["Check SQL injection", "Check XSS vulnerabilities"]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "scanned"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "code" in input_data


class SampleTool(ToolBase):
    """A concrete ToolBase for exporter tests."""

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
                    },
                    "required": ["code"],
                },
            },
        ]

    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        if function_name == "scan_code":
            return {"findings": []}
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
        tags=["security"],
        core_dependencies=["pathlib", "re"],
        config_schema={"required": ["code"], "properties": {"code": {"type": "string"}}},
    )
    skill = SampleSkill(metadata)
    skill._examples = [
        {"input": "SELECT * FROM users", "output": "SQL injection found"},
    ]
    return skill


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
            "properties": {"code": {"type": "string", "description": "The code to scan"}},
        },
        "mcp_config": {
            "transport": "stdio",
            "tools": ["scan_code"],
        },
        "when_to_use": "Use when you need to scan code for security issues",
    }


@pytest.fixture
def all_generators() -> Dict[str, FormatGenerator]:
    """Return all five generators."""
    return {
        "claude": ClaudeFormatGenerator(FORMATS_DIR / "claude"),
        "zcode": ZCodeFormatGenerator(FORMATS_DIR / "zcode"),
        "cursor": CursorFormatGenerator(FORMATS_DIR / "cursor"),
        "reasionix": ReasionixFormatGenerator(FORMATS_DIR / "reasionix"),
        "mcp": MCPFormatGenerator(FORMATS_DIR / "mcp"),
    }


@pytest.fixture
def all_validators() -> Dict[str, FormatValidator]:
    """Return all four validators."""
    return {
        "claude": ClaudeFormatValidator(),
        "zcode": ZCodeFormatValidator(),
        "cursor": CursorFormatValidator(),
        "mcp": MCPFormatValidator(),
    }


@pytest.fixture
def exporter(
    all_generators: Dict[str, FormatGenerator],
    all_validators: Dict[str, FormatValidator],
) -> ComponentExporter:
    """Return a fully configured ComponentExporter."""
    return ComponentExporter(generators=all_generators, validators=all_validators)


# ── Export Tests ───────────────────────────────────────────────────────────────


class TestComponentExporter:
    """Test ComponentExporter export functionality."""

    def test_export_with_all_tools(
        self,
        exporter: ComponentExporter,
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Exporting a skill to all five tools should return results for each."""
        target_tools = ["claude", "zcode", "cursor", "reasionix", "mcp"]
        results = exporter.export(sample_skill, sample_manifest, target_tools, tmp_path)

        # All tools should have a result
        assert len(results) == 5
        for tool in target_tools:
            assert tool in results

        # At least claude, zcode, cursor should be valid (they have validators)
        assert results["claude"].valid is True
        assert results["zcode"].valid is True
        assert results["cursor"].valid is True
        assert results["mcp"].valid is True

    def test_export_with_single_tool(
        self,
        exporter: ComponentExporter,
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Exporting a skill to just one tool should return one result."""
        results = exporter.export(sample_skill, sample_manifest, ["claude"], tmp_path)
        assert len(results) == 1
        assert "claude" in results
        assert results["claude"].valid is True

    def test_export_with_unsupported_tool(
        self,
        exporter: ComponentExporter,
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Exporting to an unsupported tool should record an error result."""
        results = exporter.export(
            sample_skill,
            sample_manifest,
            ["claude", "nonexistent_tool"],
            tmp_path,
        )
        assert len(results) == 2
        assert results["claude"].valid is True
        assert results["nonexistent_tool"].valid is False
        assert any("Unsupported" in e for e in results["nonexistent_tool"].errors)

    def test_export_writes_files_to_disk(
        self,
        exporter: ComponentExporter,
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Export should write generated files to the output directory."""
        exporter.export(sample_skill, sample_manifest, ["claude"], tmp_path)

        # Check that files were written
        claude_dir = tmp_path / "formats" / "claude"
        assert claude_dir.exists()
        assert (claude_dir / "SKILL.md").exists()
        assert (claude_dir / "plugin_config.json").exists()

        # Check file content
        skill_md = (claude_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "security_scanner" in skill_md

    def test_export_with_tool_component(
        self,
        exporter: ComponentExporter,
        sample_tool: SampleTool,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Exporting a ToolBase should produce valid results."""
        tool_manifest = {
            "name": "security_tool",
            "type": "tool",
            "version": "1.0.0",
            "description": "Security scanning tool",
            "core_dependencies": ["pathlib"],
            "mcp_config": {
                "transport": "stdio",
                "tools": ["scan_code"],
            },
        }
        results = exporter.export(
            sample_tool,
            tool_manifest,
            ["claude", "mcp"],
            tmp_path,
        )
        assert "claude" in results
        assert "mcp" in results

    def test_create_default_returns_configured_exporter(self) -> None:
        """create_default() should return an exporter with all generators and validators."""
        exporter = ComponentExporter.create_default()
        assert len(exporter.generators) == 5
        assert len(exporter.validators) == 4
        assert "claude" in exporter.generators
        assert "zcode" in exporter.generators
        assert "cursor" in exporter.generators
        assert "reasionix" in exporter.generators
        assert "mcp" in exporter.generators
        assert "claude" in exporter.validators
        assert "zcode" in exporter.validators
        assert "cursor" in exporter.validators
        assert "mcp" in exporter.validators


class TestPartialFailure:
    """Test that the exporter handles partial failures gracefully."""

    def test_one_tool_generation_fails(
        self,
        all_validators: Dict[str, FormatValidator],
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """If one generator fails, others should still succeed."""

        # Create a generator that always raises an error
        class FailingGenerator(FormatGenerator):
            tool_name = "failing_tool"

            def generate(self, component, manifest):
                raise FormatGenerationError("Intentional failure")

        generators = {
            "claude": ClaudeFormatGenerator(FORMATS_DIR / "claude"),
            "failing_tool": FailingGenerator(FORMATS_DIR / "claude"),  # Fails on purpose
        }

        exporter = ComponentExporter(generators=generators, validators=all_validators)
        results = exporter.export(
            sample_skill,
            sample_manifest,
            ["claude", "failing_tool"],
            tmp_path,
        )

        # Claude should succeed
        assert results["claude"].valid is True

        # Failing tool should have error result
        assert results["failing_tool"].valid is False
        assert any("Generation failed" in e for e in results["failing_tool"].errors)

    def test_generator_error_does_not_break_other_tools(
        self,
        all_validators: Dict[str, FormatValidator],
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """A failing generator should not prevent other tools from working."""

        class FailingGenerator(FormatGenerator):
            tool_name = "bad"

            def generate(self, component, manifest):
                raise RuntimeError("Unexpected error")

        generators = {
            "claude": ClaudeFormatGenerator(FORMATS_DIR / "claude"),
            "zcode": ZCodeFormatGenerator(FORMATS_DIR / "zcode"),
            "bad": FailingGenerator(FORMATS_DIR / "claude"),
        }

        exporter = ComponentExporter(generators=generators, validators=all_validators)
        results = exporter.export(
            sample_skill,
            sample_manifest,
            ["claude", "zcode", "bad"],
            tmp_path,
        )

        assert results["claude"].valid is True
        assert results["zcode"].valid is True
        assert results["bad"].valid is False


class TestWriteFiles:
    """Test _write_files helper method."""

    def test_write_files_creates_directories(
        self,
        exporter: ComponentExporter,
        tmp_path: Path,
    ) -> None:
        """_write_files should create necessary parent directories."""
        generated = {
            "subdir/nested/file.txt": "hello world",
        }
        output_dir = tmp_path / "formats" / "test_tool"

        exporter._write_files(generated, output_dir)

        # Check that nested directory was created
        nested_file = output_dir / "subdir" / "nested" / "file.txt"
        assert nested_file.exists()
        assert nested_file.read_text(encoding="utf-8") == "hello world"

    def test_write_files_creates_top_level_files(
        self,
        exporter: ComponentExporter,
        tmp_path: Path,
    ) -> None:
        """_write_files should create files at the top level of output_dir."""
        generated = {
            "SKILL.md": "# Skill content",
            "plugin_config.json": '{"name": "test"}',
        }
        output_dir = tmp_path / "formats" / "claude"

        exporter._write_files(generated, output_dir)

        assert (output_dir / "SKILL.md").exists()
        assert (output_dir / "plugin_config.json").exists()
        assert (output_dir / "SKILL.md").read_text(encoding="utf-8") == "# Skill content"

    def test_write_files_utf8_encoding(
        self,
        exporter: ComponentExporter,
        tmp_path: Path,
    ) -> None:
        """_write_files should write files with UTF-8 encoding."""
        generated = {
            "unicode.txt": "Chinese: 你好世界\nEmoji: test",
        }
        output_dir = tmp_path / "formats" / "test"

        exporter._write_files(generated, output_dir)

        content = (output_dir / "unicode.txt").read_text(encoding="utf-8")
        assert "你好世界" in content


class TestExporterNoValidator:
    """Test exporter behavior when no validator exists for a tool."""

    def test_export_with_no_validator(
        self,
        all_generators: Dict[str, FormatGenerator],
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Exporting to a tool without a validator should return valid=True."""
        # Only include validators for claude and mcp, not reasionix
        validators = {
            "claude": ClaudeFormatValidator(),
            "mcp": MCPFormatValidator(),
        }

        exporter = ComponentExporter(generators=all_generators, validators=validators)
        results = exporter.export(
            sample_skill,
            sample_manifest,
            ["reasionix"],
            tmp_path,
        )

        # reasionix has no validator, so it should be marked valid
        assert "reasionix" in results
        assert results["reasionix"].valid is True

    def test_reasionix_files_written(
        self,
        all_generators: Dict[str, FormatGenerator],
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Exporting to reasionix should write files even though it has no validator."""
        validators = {
            "claude": ClaudeFormatValidator(),
            "mcp": MCPFormatValidator(),
        }

        exporter = ComponentExporter(generators=all_generators, validators=validators)
        exporter.export(
            sample_skill,
            sample_manifest,
            ["reasionix"],
            tmp_path,
        )

        reasionix_dir = tmp_path / "formats" / "reasionix"
        assert reasionix_dir.exists()


class TestExportEndToEnd:
    """End-to-end export tests using create_default()."""

    def test_full_export_skill(
        self,
        sample_skill: SampleSkill,
        sample_manifest: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Full export of a skill using create_default() should work."""
        exporter = ComponentExporter.create_default()
        target_tools = ["claude", "zcode", "cursor", "mcp"]
        results = exporter.export(sample_skill, sample_manifest, target_tools, tmp_path)

        # All should have results
        assert len(results) == 4

        # All should be valid or have only warnings
        for tool, result in results.items():
            assert result.valid is True, f"{tool} validation failed: {result.errors}"

        # Files should exist on disk
        for tool in target_tools:
            tool_dir = tmp_path / "formats" / tool
            assert tool_dir.exists()
            assert len(list(tool_dir.iterdir())) > 0

    def test_full_export_tool(
        self,
        sample_tool: SampleTool,
        tmp_path: Path,
    ) -> None:
        """Full export of a tool using create_default() should work."""
        exporter = ComponentExporter.create_default()
        tool_manifest = {
            "name": "security_tool",
            "type": "tool",
            "version": "1.0.0",
            "description": "Security scanning tool",
            "core_dependencies": ["pathlib"],
            "mcp_config": {
                "transport": "stdio",
                "tools": ["scan_code"],
            },
        }
        results = exporter.export(
            sample_tool,
            tool_manifest,
            ["claude", "mcp"],
            tmp_path,
        )
        assert results["claude"].valid is True
        assert results["mcp"].valid is True
