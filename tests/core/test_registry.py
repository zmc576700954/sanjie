"""Tests for core/shared/registry.py -- ComponentRegistry."""

from __future__ import annotations

import pytest

from core.shared.base import ComponentMetadata, ComponentType, CoreComponent
from core.shared.errors import ComponentNotFoundError, DuplicateComponentError
from core.shared.registry import ComponentRegistry
from typing import Any, Dict


class _SimpleComponent(CoreComponent):
    """Minimal concrete component for registry tests."""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"name": self.name}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True


def _make_component(name: str, ctype: ComponentType) -> _SimpleComponent:
    return _SimpleComponent(ComponentMetadata(name=name, type=ctype))


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset the singleton registry before each test to avoid cross-test contamination."""
    ComponentRegistry._instance = None
    yield
    ComponentRegistry._instance = None


class TestComponentRegistry:
    """Tests for the ComponentRegistry singleton."""

    def test_singleton(self) -> None:
        r1 = ComponentRegistry()
        r2 = ComponentRegistry()
        assert r1 is r2

    def test_register_and_get(self) -> None:
        registry = ComponentRegistry()
        comp = _make_component("my_skill", ComponentType.SKILL)
        registry.register(comp)
        assert registry.get("my_skill") is comp

    def test_duplicate_registration_raises(self) -> None:
        registry = ComponentRegistry()
        comp1 = _make_component("dup", ComponentType.TOOL)
        comp2 = _make_component("dup", ComponentType.TOOL)
        registry.register(comp1)
        with pytest.raises(DuplicateComponentError):
            registry.register(comp2)

    def test_get_nonexistent_raises(self) -> None:
        registry = ComponentRegistry()
        with pytest.raises(ComponentNotFoundError):
            registry.get("does_not_exist")

    def test_list_by_type(self) -> None:
        registry = ComponentRegistry()
        skill1 = _make_component("s1", ComponentType.SKILL)
        skill2 = _make_component("s2", ComponentType.SKILL)
        tool1 = _make_component("t1", ComponentType.TOOL)
        registry.register(skill1)
        registry.register(skill2)
        registry.register(tool1)

        skills = registry.list_by_type(ComponentType.SKILL)
        assert len(skills) == 2
        assert skill1 in skills
        assert skill2 in skills

        tools = registry.list_by_type(ComponentType.TOOL)
        assert len(tools) == 1
        assert tool1 in tools

        agents = registry.list_by_type(ComponentType.AGENT)
        assert len(agents) == 0

    def test_list_all(self) -> None:
        registry = ComponentRegistry()
        s1 = _make_component("s1", ComponentType.SKILL)
        t1 = _make_component("t1", ComponentType.TOOL)
        a1 = _make_component("a1", ComponentType.AGENT)
        registry.register(s1)
        registry.register(t1)
        registry.register(a1)

        all_comps = registry.list_all()
        assert len(all_comps) == 3
        assert s1 in all_comps
        assert t1 in all_comps
        assert a1 in all_comps

    def test_list_all_empty(self) -> None:
        registry = ComponentRegistry()
        assert registry.list_all() == []

    def test_unregister(self) -> None:
        registry = ComponentRegistry()
        comp = _make_component("remove_me", ComponentType.SKILL)
        registry.register(comp)
        assert registry.get("remove_me") is comp

        registry.unregister("remove_me")
        with pytest.raises(ComponentNotFoundError):
            registry.get("remove_me")

    def test_unregister_nonexistent_is_noop(self) -> None:
        registry = ComponentRegistry()
        # Should not raise
        registry.unregister("ghost")

    def test_unregister_removes_from_type_index(self) -> None:
        registry = ComponentRegistry()
        s1 = _make_component("s1", ComponentType.SKILL)
        s2 = _make_component("s2", ComponentType.SKILL)
        registry.register(s1)
        registry.register(s2)

        registry.unregister("s1")
        skills = registry.list_by_type(ComponentType.SKILL)
        assert len(skills) == 1
        assert skills[0].name == "s2"
