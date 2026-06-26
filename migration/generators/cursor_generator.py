"""Cursor format generator.

Generates SKILL.md (with cursorVersion frontmatter) and cursor_config.json
from core components for Cursor AI integration. Nearly identical to Claude
format with minor differences (cursorVersion, cursorRules config).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.shared.base import CoreComponent
from core.agents.base import AgentBase
from core.skills.base import SkillBase
from core.tools.base import ToolBase
from migration.generators.base import FormatGenerator


class CursorFormatGenerator(FormatGenerator):
    """Generate Cursor format files from a core component.

    Produces:
        - ``SKILL.md``: Skill definition with YAML frontmatter (includes cursorVersion).
        - ``cursor_config.json``: Cursor configuration with MCP servers and cursor rules.
    """

    tool_name = "cursor"

    def generate(self, component: CoreComponent, manifest: Dict[str, Any]) -> Dict[str, str]:
        """Generate Cursor format files from a core component.

        Args:
            component: The core component (SkillBase, AgentBase, or ToolBase).
            manifest: The manifest.json content.

        Returns:
            A dictionary mapping relative file paths to generated content.
            Keys include ``"SKILL.md"`` and ``"cursor_config.json"``.
        """
        variables = self._extract_variables(component, manifest)
        output: Dict[str, str] = {}

        # Generate SKILL.md (with cursorVersion in frontmatter)
        skill_md = self._render_template("SKILL.md", variables)
        output["SKILL.md"] = skill_md

        # Generate cursor_config.json
        config_vars = self._build_config_variables(variables, manifest)
        cursor_config = self._render_template("cursor_config.json", config_vars)
        output["cursor_config.json"] = cursor_config

        return output

    def _extract_variables(
        self,
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract variables with Cursor-specific enhancements.

        Extends base extraction with cursorVersion and tools formatting.
        The cursorVersion is hardcoded in the template, but we ensure
        the tools variable is populated for Cursor's Tools section.
        """
        variables = super()._extract_variables(component, manifest)

        # Cursor-specific: format tools section
        if isinstance(component, SkillBase):
            variables["examples"] = self._format_examples(component.examples)

        if isinstance(component, ToolBase):
            variables["tools"] = self._format_tools(component.function_definitions)

        if isinstance(component, AgentBase):
            variables["tools"] = self._format_tools(component.available_tools)

        return variables

    def _build_config_variables(
        self,
        variables: Dict[str, Any],
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build variables for the cursor_config.json template.

        Formats MCP config and cursor rules for Cursor's configuration.
        """
        mcp_config = manifest.get("mcp_config", {})

        return {
            "name": variables["name"],
            "mcp_config": json.dumps(mcp_config, indent=2),
        }
