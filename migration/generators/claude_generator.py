"""Claude Code/Desktop format generator.

Generates SKILL.md (with YAML frontmatter), plugin_config.json, and
slash command definitions from core components for Claude integration.
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


class ClaudeFormatGenerator(FormatGenerator):
    """Generate Claude Code/Desktop format files from a core component.

    Produces:
        - ``SKILL.md``: Skill definition with YAML frontmatter.
        - ``plugin_config.json``: Plugin configuration with MCP server mapping.
        - ``slash_commands/template.md``: Slash command definition (for skills).
    """

    tool_name = "claude"

    def generate(self, component: CoreComponent, manifest: Dict[str, Any]) -> Dict[str, str]:
        """Generate Claude format files from a core component.

        Args:
            component: The core component (SkillBase, AgentBase, or ToolBase).
            manifest: The manifest.json content.

        Returns:
            A dictionary mapping relative file paths to generated content.
            Keys include ``"SKILL.md"``, ``"plugin_config.json"``, and
            optionally ``"slash_commands/template.md"``.
        """
        variables = self._extract_variables(component, manifest)
        output: Dict[str, str] = {}

        # Generate SKILL.md
        skill_md = self._render_template("SKILL.md", variables)
        output["SKILL.md"] = skill_md

        # Generate plugin_config.json
        plugin_vars = self._build_plugin_variables(variables, manifest)
        plugin_config = self._render_template("plugin_config.json", plugin_vars)
        output["plugin_config.json"] = plugin_config

        # Generate slash command for skills
        if isinstance(component, SkillBase):
            slash_vars = self._build_slash_variables(variables)
            if "slash_commands/template.md" in self._templates:
                slash_cmd = self._render_template("slash_commands/template.md", slash_vars)
                output["slash_commands/template.md"] = slash_cmd

        return output

    def _extract_variables(
        self,
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract variables with Claude-specific enhancements.

        Extends the base extraction with Claude-specific formatting for
        checklist items and examples.
        """
        variables = super()._extract_variables(component, manifest)

        # Claude-specific: ensure checklist is markdown-formatted
        if isinstance(component, SkillBase):
            checklist_items = component.get_checklist()
            variables["checklist"] = self._format_checklist(checklist_items)
            variables["examples"] = self._format_examples(component.examples)
            variables["when_to_use"] = manifest.get(
                "when_to_use",
                f"Use {component.name} when you need to {component.metadata.description.lower()}",
            )

        if isinstance(component, AgentBase):
            variables["when_to_use"] = manifest.get(
                "when_to_use",
                f"Use {component.name} for tasks requiring {component.metadata.description.lower()}",
            )

        return variables

    def _build_plugin_variables(
        self,
        variables: Dict[str, Any],
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build variables for the plugin_config.json template.

        Formats the mcp_config as a proper JSON object for the MCP servers
        section of the plugin configuration.
        """
        mcp_config = manifest.get("mcp_config", {})
        if not mcp_config:
            mcp_config = {}

        return {
            "name": variables["name"],
            "version": variables["version"],
            "description": variables["description"],
            "type": variables["type"],
            "mcp_config": json.dumps(mcp_config, indent=2),
        }

    def _build_slash_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Build variables for the slash command template."""
        return {
            "name": variables["name"],
            "description": variables["description"],
            "instructions": variables["instructions"],
            "examples": variables["examples"],
        }
