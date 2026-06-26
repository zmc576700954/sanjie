"""ZCode format generator.

Generates Command.md and command_config.json from core components
for ZCode custom command integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.shared.base import CoreComponent
from core.skills.base import SkillBase
from core.tools.base import ToolBase
from migration.generators.base import FormatGenerator


class ZCodeFormatGenerator(FormatGenerator):
    """Generate ZCode format files from a core component.

    Produces:
        - ``Command.md``: Command definition with usage, instructions, and examples.
        - ``command_config/template.json``: Command configuration with argument mapping.
    """

    tool_name = "zcode"

    def generate(self, component: CoreComponent, manifest: Dict[str, Any]) -> Dict[str, str]:
        """Generate ZCode format files from a core component.

        Args:
            component: The core component (typically SkillBase).
            manifest: The manifest.json content.

        Returns:
            A dictionary mapping relative file paths to generated content.
            Keys include ``"Command.md"`` and ``"command_config/template.json"``.
        """
        variables = self._extract_variables(component, manifest)
        output: Dict[str, str] = {}

        # Generate Command.md
        command_vars = self._build_command_variables(variables, component)
        command_md = self._render_template("Command.md", command_vars)
        output["Command.md"] = command_md

        # Generate command_config.json
        config_vars = self._build_config_variables(variables, manifest)
        if "command_config/template.json" in self._templates:
            config_json = self._render_template("command_config/template.json", config_vars)
            output["command_config/template.json"] = config_json

        return output

    def _extract_variables(
        self,
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract variables with ZCode-specific enhancements.

        Converts skill instructions to command-oriented format.
        """
        variables = super()._extract_variables(component, manifest)

        if isinstance(component, SkillBase):
            # ZCode uses checklist in Command.md format
            variables["checklist"] = self._format_checklist(component.get_checklist())
            variables["examples"] = self._format_examples(component.examples)

        return variables

    def _build_command_variables(
        self,
        variables: Dict[str, Any],
        component: CoreComponent,
    ) -> Dict[str, Any]:
        """Build variables for the Command.md template.

        Converts skill instructions to command-oriented format.
        """
        cmd_vars = dict(variables)

        # Convert instructions to command-oriented format
        instructions = cmd_vars.get("instructions", "")
        if instructions and isinstance(component, SkillBase):
            # Prefix instructions with command context
            cmd_vars["instructions"] = instructions

        return cmd_vars

    def _build_config_variables(
        self,
        variables: Dict[str, Any],
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build variables for the command_config.json template.

        Maps the config_schema from manifest to command arguments format.
        """
        config_schema = manifest.get("config_schema", {})
        core_dependencies = manifest.get("core_dependencies", [])

        # Map config_schema properties to command arguments
        arguments = self._map_config_to_arguments(config_schema)

        return {
            "name": variables["name"],
            "description": variables["description"],
            "config_schema": json.dumps(arguments, indent=2),
            "core_dependencies": json.dumps(core_dependencies),
        }

    @staticmethod
    def _map_config_to_arguments(config_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Map a JSON Schema config_schema to ZCode command arguments format.

        Converts JSON Schema properties into a simplified argument format
        that ZCode expects.

        Args:
            config_schema: The JSON Schema from manifest.json.

        Returns:
            A dictionary of arguments suitable for ZCode command config.
        """
        if not config_schema:
            return {}

        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        arguments: Dict[str, Any] = {}
        for prop_name, prop_def in properties.items():
            arguments[prop_name] = {
                "type": prop_def.get("type", "string"),
                "description": prop_def.get("description", ""),
                "required": prop_name in required,
            }

        return arguments
