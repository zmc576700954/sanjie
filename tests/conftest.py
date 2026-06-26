"""Shared test fixtures for agents_develop tests."""

from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path

import pytest

from core.shared.base import ComponentMetadata, ComponentType, CoreComponent
from core.agents.base import AgentBase
from core.skills.base import SkillBase
from core.tools.base import ToolBase


# ── Concrete subclasses for testing ───────────────────────────────────────────


class ConcreteSkill(SkillBase):
    """A concrete SkillBase subclass for testing."""

    @property
    def instructions(self) -> str:
        return "Test skill instructions"

    def get_checklist(self) -> List[str]:
        return ["Step 1", "Step 2", "Step 3"]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": f"executed with {input_data}"}


class ConcreteAgent(AgentBase):
    """A concrete AgentBase subclass for testing."""

    @property
    def system_prompt(self) -> str:
        return "You are a test agent."

    @property
    def available_tools(self) -> List[Dict[str, Any]]:
        return [{"name": "test_tool", "description": "A test tool"}]

    def plan(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"action": "do_something", "task": task}]

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"needs_adjustment": False, "assessment": "ok"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "task" in input_data


class ConcreteTool(ToolBase):
    """A concrete ToolBase subclass for testing."""

    @property
    def function_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "test_func",
                "description": "A test function",
                "inputSchema": {"type": "object", "properties": {"x": {"type": "integer"}}},
            }
        ]

    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        if function_name == "test_func":
            return arguments.get("x", 0) * 2
        return None

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "function" in input_data


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_metadata() -> ComponentMetadata:
    """Return a sample ComponentMetadata for testing."""
    return ComponentMetadata(
        name="test_component",
        type=ComponentType.SKILL,
        version="1.0.0",
        description="A test component",
        author="Test Author",
        tags=["test"],
        config_schema={"required": ["input_text"]},
    )


@pytest.fixture
def sample_skill() -> ConcreteSkill:
    """Return a concrete SkillBase instance for testing."""
    metadata = ComponentMetadata(
        name="test_skill",
        type=ComponentType.SKILL,
        version="1.0.0",
        description="A test skill",
        config_schema={"required": ["input_text"]},
    )
    skill = ConcreteSkill(metadata)
    skill._examples = [
        {"input": "hello", "output": "HELLO"},
        {"input": "world", "output": "WORLD"},
    ]
    return skill


@pytest.fixture
def sample_agent() -> ConcreteAgent:
    """Return a concrete AgentBase instance for testing."""
    metadata = ComponentMetadata(
        name="test_agent",
        type=ComponentType.AGENT,
        version="1.0.0",
        description="A test agent",
    )
    return ConcreteAgent(metadata)


@pytest.fixture
def sample_tool() -> ConcreteTool:
    """Return a concrete ToolBase instance for testing."""
    metadata = ComponentMetadata(
        name="test_tool",
        type=ComponentType.TOOL,
        version="1.0.0",
        description="A test tool",
    )
    return ConcreteTool(metadata)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for file-based tests."""
    return tmp_path
