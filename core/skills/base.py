"""Skill base class -- defines the contract for all skill components.

A skill is a reusable module with instructions, a checklist, and examples
that can be migrated to different tool formats (SKILL.md, Command.md, etc.).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, CoreComponent


class SkillBase(CoreComponent):
    """Base class for skill components.

    Skills encapsulate reusable instructions that can be rendered into
    tool-specific formats (SKILL.md for Claude/Cursor, Command.md for ZCode, etc.).

    Subclasses must implement:
        - instructions: The skill's usage instructions.
        - get_checklist(): A list of checklist items for execution.
    """

    def __init__(self, metadata: ComponentMetadata) -> None:
        super().__init__(metadata)
        self._instructions: str = ""
        self._examples: List[Dict[str, str]] = []

    @property
    @abstractmethod
    def instructions(self) -> str:
        """Return the skill's usage instructions.

        These instructions will be converted into SKILL.md / Command.md content
        by the format generators.
        """

    @property
    def examples(self) -> List[Dict[str, str]]:
        """Return usage examples for the skill.

        Each example is a dict with ``"input"`` and ``"output"`` keys.
        """
        return self._examples

    @abstractmethod
    def get_checklist(self) -> List[str]:
        """Return the skill's execution checklist.

        Returns:
            A list of checklist item strings.
        """

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against the component's config schema.

        Checks that all keys listed in the config schema's ``"required"``
        array are present in *input_data*.

        Args:
            input_data: The input dictionary to validate.

        Returns:
            True if all required keys are present, False otherwise.
        """
        required = self._metadata.config_schema.get("required", [])
        return all(key in input_data for key in required)

    def to_skill_md(self) -> str:
        """Generate tool-agnostic SKILL.md content.

        The output is a plain-text representation of the skill that can be
        further adapted by format generators for specific tools.

        Returns:
            The SKILL.md content as a string.
        """
        checklist = "\n".join(f"- [ ] {item}" for item in self.get_checklist())
        examples_text = ""
        for ex in self.examples:
            examples_text += f"\n**Input:** {ex.get('input', '')}\n**Output:** {ex.get('output', '')}\n"

        return f"""# {self.name}

{self._metadata.description}

## Instructions

{self.instructions}

## Checklist

{checklist}

## Examples
{examples_text}
"""
