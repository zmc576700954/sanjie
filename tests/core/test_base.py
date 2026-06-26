"""Tests for core/shared/base.py -- ComponentMetadata, ComponentType, CoreComponent."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from core.shared.base import ComponentMetadata, ComponentType, CoreComponent


# ── ComponentType tests ───────────────────────────────────────────────────────


class TestComponentType:
    """Tests for the ComponentType enum."""

    def test_enum_values(self) -> None:
        assert ComponentType.AGENT.value == "agent"
        assert ComponentType.SKILL.value == "skill"
        assert ComponentType.TOOL.value == "tool"
        assert ComponentType.MCP_SERVER.value == "mcp_server"

    def test_enum_members(self) -> None:
        assert len(ComponentType) == 4

    def test_enum_from_value(self) -> None:
        assert ComponentType("skill") == ComponentType.SKILL


# ── ComponentMetadata tests ──────────────────────────────────────────────────


class TestComponentMetadata:
    """Tests for the ComponentMetadata dataclass."""

    def test_creation_with_defaults(self) -> None:
        meta = ComponentMetadata(name="my_comp", type=ComponentType.SKILL)
        assert meta.name == "my_comp"
        assert meta.type == ComponentType.SKILL
        assert meta.version == "1.0.0"
        assert meta.description == ""
        assert meta.author == ""
        assert meta.tags == []
        assert meta.core_dependencies == []
        assert meta.supported_tools == ["claude", "zcode", "cursor", "reasionix", "mcp"]
        assert meta.config_schema == {}

    def test_creation_with_all_fields(self) -> None:
        meta = ComponentMetadata(
            name="full_comp",
            type=ComponentType.TOOL,
            version="2.3.1",
            description="A full component",
            author="Dev",
            created="2025-01-01",
            updated="2025-06-25",
            tags=["a", "b"],
            core_dependencies=["requests"],
            supported_tools=["claude", "mcp"],
            config_schema={"type": "object"},
        )
        assert meta.name == "full_comp"
        assert meta.version == "2.3.1"
        assert meta.description == "A full component"
        assert meta.author == "Dev"
        assert meta.created == "2025-01-01"
        assert meta.updated == "2025-06-25"
        assert meta.tags == ["a", "b"]
        assert meta.core_dependencies == ["requests"]
        assert meta.supported_tools == ["claude", "mcp"]
        assert meta.config_schema == {"type": "object"}

    def test_default_lists_are_independent(self) -> None:
        """Ensure default mutable fields are not shared across instances."""
        m1 = ComponentMetadata(name="a", type=ComponentType.AGENT)
        m2 = ComponentMetadata(name="b", type=ComponentType.SKILL)
        m1.tags.append("shared_tag")
        assert "shared_tag" not in m2.tags


# ── CoreComponent tests ──────────────────────────────────────────────────────


class _ConcreteComponent(CoreComponent):
    """Minimal concrete subclass for testing CoreComponent."""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"echo": input_data}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "action" in input_data


class TestCoreComponent:
    """Tests for the CoreComponent ABC via a concrete subclass."""

    def test_metadata_property(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        assert comp.metadata is sample_metadata

    def test_name_property(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        assert comp.name == "test_component"

    def test_component_type_property(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        assert comp.component_type == ComponentType.SKILL

    def test_execute(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        result = comp.execute({"action": "run"})
        assert result == {"echo": {"action": "run"}}

    def test_validate_input_valid(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        assert comp.validate_input({"action": "run"}) is True

    def test_validate_input_invalid(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        assert comp.validate_input({"wrong_key": "value"}) is False

    def test_configure(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        comp.configure({"debug": True})
        assert comp._config == {"debug": True}

    def test_get_config_schema(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        schema = comp.get_config_schema()
        assert "required" in schema
        assert "input_text" in schema["required"]

    def test_to_dict(self, sample_metadata: ComponentMetadata) -> None:
        comp = _ConcreteComponent(sample_metadata)
        d = comp.to_dict()
        assert d["name"] == "test_component"
        assert d["type"] == "skill"
        assert d["version"] == "1.0.0"
        assert d["description"] == "A test component"
        assert "config_schema" in d

    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            CoreComponent(ComponentMetadata(name="x", type=ComponentType.TOOL))  # type: ignore[abstract]
