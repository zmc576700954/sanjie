"""Reasionix format generator.

Generates standalone Python scripts with Deepseek optimizations and
deepseek_config.json from core components for Reasionix integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from core.shared.base import CoreComponent
from core.skills.base import SkillBase
from core.tools.base import ToolBase
from migration.generators.base import FormatGenerator


class ReasionixFormatGenerator(FormatGenerator):
    """Generate Reasionix format files from a core component.

    Produces:
        - ``script_templates/template.py``: Standalone Python script with
          argparse-based CLI and Deepseek optimizations.
        - ``deepseek_config/template.json``: Deepseek model configuration.
    """

    tool_name = "reasionix"

    def generate(self, component: CoreComponent, manifest: Dict[str, Any]) -> Dict[str, str]:
        """Generate Reasionix format files from a core component.

        Args:
            component: The core component (SkillBase, ToolBase, etc.).
            manifest: The manifest.json content.

        Returns:
            A dictionary mapping relative file paths to generated content.
            Keys include ``"script_templates/template.py"`` and
            ``"deepseek_config/template.json"``.
        """
        variables = self._extract_variables(component, manifest)
        output: Dict[str, str] = {}

        # Generate Python script
        script_vars = self._build_script_variables(variables, component, manifest)
        script_content = self._render_template("script_templates/template.py", script_vars)
        output["script_templates/template.py"] = script_content

        # Generate deepseek_config.json
        config_vars = self._build_config_variables(variables, manifest)
        if "deepseek_config/template.json" in self._templates:
            config_content = self._render_template("deepseek_config/template.json", config_vars)
            output["deepseek_config/template.json"] = config_content

        return output

    def _extract_variables(
        self,
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract variables with Reasionix-specific enhancements.

        Converts instructions to Python comments and builds argparse definitions.
        """
        variables = super()._extract_variables(component, manifest)

        # Convert instructions to Python comments
        instructions = variables.get("instructions", "")
        variables["instructions_as_python_comments"] = self._instructions_to_comments(instructions)

        # Build argparse argument definitions from config_schema
        config_schema = manifest.get("config_schema", {})
        variables["argument_parsing"] = self._build_argparse(config_schema)

        return variables

    @staticmethod
    def _instructions_to_comments(instructions: str) -> str:
        """Convert instruction text to Python comments.

        Each line of the instructions is prefixed with ``# `` to form
        valid Python comments.

        Args:
            instructions: The instruction text to convert.

        Returns:
            The instructions as Python comments.
        """
        if not instructions:
            return "# No instructions provided"
        lines = instructions.strip().split("\n")
        return "\n".join(f"# {line}" for line in lines)

    @staticmethod
    def _build_argparse(config_schema: Dict[str, Any]) -> str:
        """Build argparse add_argument calls from config_schema.

        Converts JSON Schema properties into argparse argument definitions.

        Args:
            config_schema: The JSON Schema from manifest.json.

        Returns:
            Python code strings for argparse argument definitions.
        """
        if not config_schema:
            return "    # No arguments defined"

        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        lines: List[str] = []
        for prop_name, prop_def in properties.items():
            arg_type = prop_def.get("type", "string")
            arg_desc = prop_def.get("description", "")

            # Map JSON Schema types to Python types
            type_map = {
                "string": "str",
                "integer": "int",
                "number": "float",
                "boolean": "bool",
            }
            python_type = type_map.get(arg_type, "str")

            # Build the argparse line
            if prop_name in required:
                lines.append(
                    f'    parser.add_argument("{prop_name}", '
                    f"type={python_type}, help=\"{arg_desc}\")"
                )
            else:
                lines.append(
                    f'    parser.add_argument("--{prop_name}", '
                    f"type={python_type}, help=\"{arg_desc}\")"
                )

        return "\n".join(lines) if lines else "    # No arguments defined"

    def _build_script_variables(
        self,
        variables: Dict[str, Any],
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build variables for the script template."""
        return {
            "name": variables["name"],
            "version": variables["version"],
            "description": variables["description"],
            "instructions_as_python_comments": variables["instructions_as_python_comments"],
            "argument_parsing": variables["argument_parsing"],
        }

    def _build_config_variables(
        self,
        variables: Dict[str, Any],
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build variables for the deepseek_config.json template."""
        core_dependencies = manifest.get("core_dependencies", [])

        return {
            "name": variables["name"],
            "core_dependencies": json.dumps(core_dependencies),
        }
