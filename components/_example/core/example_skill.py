"""Example skill that demonstrates the component architecture.

This is a reference implementation showing how to create a skill component
that inherits from SkillBase and implements all required abstract methods.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.skills.base import SkillBase


class ExampleSkill(SkillBase):
    """Example skill that demonstrates the component architecture.

    This skill processes text messages and returns a formatted result.
    Use it as a template for creating new skills.
    """

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="example_skill",
            type=ComponentType.SKILL,
            version="1.0.0",
            description="Example skill that demonstrates the component architecture",
            author="agents_develop",
            tags=["example", "demo", "template"],
            supported_tools=["claude", "zcode", "mcp"],
        )
        super().__init__(metadata)
        self._examples = [
            {"input": "Hello, world!", "output": "Processed: Hello, world!"},
            {"input": "Test message", "output": "Processed: Test message"},
        ]

    @property
    def instructions(self) -> str:
        """Return the skill's usage instructions."""
        return (
            "This is an example skill. Use it as a template for creating new skills.\n"
            "The skill accepts a message input and returns a processed result.\n"
            "To use: provide a 'message' key in the input data."
        )

    def get_checklist(self) -> List[str]:
        """Return the skill's execution checklist."""
        return [
            "Step 1: Read input message",
            "Step 2: Process data",
            "Step 3: Return result",
        ]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill's core logic.

        Processes the input message and returns a formatted result.

        Args:
            input_data: Input dictionary. Should contain a 'message' key.

        Returns:
            Dictionary containing the processed result.
        """
        message = input_data.get("message", "Hello")
        return {"result": f"Processed: {message}"}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data meets the skill's requirements.

        Args:
            input_data: The input dictionary to validate.

        Returns:
            True if the input is valid, False otherwise.
        """
        return True
