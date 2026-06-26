"""Format generator base class -- defines the contract for all format generators.

Each generator loads templates from a tool-specific directory, extracts variables
from a core component and manifest, renders templates, and returns a mapping
of relative file paths to generated content.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.shared.base import (
    ComponentMetadata,
    ComponentType,
    CoreComponent,
)
from core.agents.base import AgentBase
from core.skills.base import SkillBase
from core.tools.base import ToolBase
from core.shared.errors import FormatGenerationError, TemplateError


class FormatGenerator(ABC):
    """Abstract base class for format generators.

    Subclasses must:
        - Set the ``tool_name`` class attribute (e.g. "claude", "zcode").
        - Implement ``generate()`` to produce tool-specific output files.

    The base class handles:
        - Loading ``.template`` files from the template directory.
        - Loading ``.json`` template files (for config templates).
        - Simple ``{{variable}}`` substitution via ``_render_template()``.
        - Common variable extraction via ``_extract_variables()``.
    """

    tool_name: str = ""

    def __init__(self, template_dir: Path) -> None:
        """Initialize the generator and load templates from *template_dir*.

        Args:
            template_dir: Path to the directory containing template files
                          for this tool format.
        """
        self.template_dir = template_dir
        self._templates: Dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all template files from the template directory.

        Reads ``*.template`` files using their stem as the template key
        (e.g. ``SKILL.md.template`` becomes ``"SKILL.md"``). Also reads
        ``*.json`` files in the template directory using their filename
        as the key (e.g. ``plugin_config.json`` becomes ``"plugin_config.json"``).

        For nested subdirectories, ``*.template`` and ``*.json`` files are
        also loaded with their relative path as the key.
        """
        if not self.template_dir.exists():
            return

        # Load .template files from the top-level directory
        for template_file in self.template_dir.glob("*.template"):
            key = template_file.stem  # e.g. "SKILL.md" from "SKILL.md.template"
            self._templates[key] = template_file.read_text(encoding="utf-8")

        # Load .json template files from the top-level directory
        for json_file in self.template_dir.glob("*.json"):
            key = json_file.name  # e.g. "plugin_config.json"
            self._templates[key] = json_file.read_text(encoding="utf-8")

        # Load files from subdirectories (one level deep)
        for subdir in self.template_dir.iterdir():
            if subdir.is_dir():
                for template_file in subdir.glob("*.template"):
                    key = f"{subdir.name}/{template_file.stem}"
                    self._templates[key] = template_file.read_text(encoding="utf-8")
                for json_file in subdir.glob("*.json"):
                    key = f"{subdir.name}/{json_file.name}"
                    self._templates[key] = json_file.read_text(encoding="utf-8")
                for other_file in subdir.glob("*.py"):
                    key = f"{subdir.name}/{other_file.name}"
                    self._templates[key] = other_file.read_text(encoding="utf-8")
                for other_file in subdir.glob("*.md"):
                    key = f"{subdir.name}/{other_file.name}"
                    self._templates[key] = other_file.read_text(encoding="utf-8")

    @abstractmethod
    def generate(self, component: CoreComponent, manifest: Dict[str, Any]) -> Dict[str, str]:
        """Generate tool-specific format files from a core component.

        Args:
            component: The core component instance to generate formats for.
            manifest: The manifest.json content providing metadata.

        Returns:
            A dictionary mapping relative file paths to generated file content.
            For example: ``{"SKILL.md": "...", "plugin_config.json": "..."}``
        """

    def _render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Render a template by performing simple {{var}} substitution.

        Replaces all ``{{key}}`` placeholders in the template with the
        corresponding value from *variables*. Missing variables are replaced
        with an empty string.

        Args:
            template_name: The key used when loading the template
                           (e.g. ``"SKILL.md"`` or ``"plugin_config.json"``).
            variables: A dictionary of variable names to values.

        Returns:
            The rendered template content as a string.

        Raises:
            TemplateError: If the template is not found.
        """
        template = self._templates.get(template_name)
        if template is None:
            raise TemplateError(f"Template '{template_name}' not found for tool '{self.tool_name}'")

        result = template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))

        # Remove any remaining unreplaced placeholders
        result = re.sub(r"\{\{(\w+)\}\}", "", result)

        return result

    def _extract_variables(
        self,
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract common variables from a component and manifest for templates.

        This method provides a baseline set of variables that most generators
        need. Subclasses can override or extend this for tool-specific variables.

        For SkillBase components, extracts instructions, checklist, examples.
        For AgentBase components, extracts system_prompt, available_tools.
        For ToolBase components, extracts function_definitions.

        Args:
            component: The core component instance.
            manifest: The manifest.json content.

        Returns:
            A dictionary of template variable names to their extracted values.
        """
        variables: Dict[str, Any] = {
            "name": component.name,
            "type": component.component_type.value,
            "version": component.metadata.version,
            "description": component.metadata.description,
            "instructions": "",
            "checklist": "",
            "examples": "",
            "tools": "",
            "system_prompt": "",
            "config_schema": json.dumps(manifest.get("config_schema", {}), indent=2),
            "dependencies": json.dumps(component.metadata.core_dependencies),
            "core_dependencies": json.dumps(component.metadata.core_dependencies),
            "mcp_config": json.dumps(manifest.get("mcp_config", {}), indent=2),
            "when_to_use": manifest.get("when_to_use", component.metadata.description),
            "mcp_transport": manifest.get("mcp_config", {}).get("transport", "stdio"),
        }

        # Extract type-specific variables
        if isinstance(component, SkillBase):
            variables["instructions"] = component.instructions
            variables["checklist"] = self._format_checklist(component.get_checklist())
            variables["examples"] = self._format_examples(component.examples)

        if isinstance(component, AgentBase):
            variables["system_prompt"] = component.system_prompt
            variables["tools"] = self._format_tools(component.available_tools)
            # For agents, instructions come from the system prompt
            if not variables["instructions"]:
                variables["instructions"] = component.system_prompt

        if isinstance(component, ToolBase):
            variables["tools"] = self._format_tools(component.function_definitions)
            # For tools, instructions come from function descriptions
            if not variables["instructions"]:
                func_descs = [
                    f"- {f['name']}: {f.get('description', '')}"
                    for f in component.function_definitions
                ]
                variables["instructions"] = "\n".join(func_descs)

        return variables

    @staticmethod
    def _format_checklist(checklist: List[str]) -> str:
        """Format a checklist as a markdown bullet list with checkboxes.

        Args:
            checklist: A list of checklist item strings.

        Returns:
            A markdown-formatted checklist string.
        """
        return "\n".join(f"- [ ] {item}" for item in checklist)

    @staticmethod
    def _format_examples(examples: List[Dict[str, str]]) -> str:
        """Format examples as markdown with input/output pairs.

        Args:
            examples: A list of dicts with "input" and "output" keys.

        Returns:
            A markdown-formatted examples string.
        """
        if not examples:
            return ""
        parts: List[str] = []
        for ex in examples:
            input_text = ex.get("input", "")
            output_text = ex.get("output", "")
            parts.append(f"**Input:** {input_text}\n**Output:** {output_text}")
        return "\n\n".join(parts)

    @staticmethod
    def _format_tools(tools: List[Dict[str, Any]]) -> str:
        """Format tool definitions as a markdown list.

        Args:
            tools: A list of tool definition dictionaries.

        Returns:
            A markdown-formatted tools string.
        """
        if not tools:
            return ""
        parts: List[str] = []
        for tool in tools:
            name = tool.get("name", "unnamed")
            desc = tool.get("description", "")
            parts.append(f"- **{name}**: {desc}")
        return "\n".join(parts)
