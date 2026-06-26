"""ZCode format validator.

Validates that generated ZCode format files conform to the expected structure:
- Command.md must have a # heading matching the component name and a Usage section.
- command_config/template.json must be valid JSON with name and description.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from migration.validators.base import FormatValidator, ValidationResult


class ZCodeFormatValidator(FormatValidator):
    """Validate generated ZCode format files.

    Checks:
        - Command.md exists and is non-empty.
        - Command.md has a ``#`` heading matching the component name.
        - Command.md has a ``## Usage`` section.
        - command_config/template.json exists and is valid JSON.
        - command_config/template.json has ``name`` and ``description`` fields.

    Warnings:
        - Missing ``## Examples`` section in Command.md.
    """

    tool_name = "zcode"

    REQUIRED_FILES: List[str] = ["Command.md", "command_config/template.json"]

    def validate(
        self,
        generated_files: Dict[str, str],
        manifest: Dict[str, Any],
    ) -> ValidationResult:
        """Validate ZCode format files.

        Args:
            generated_files: The generated file content mapping.
            manifest: The manifest.json content.

        Returns:
            A ValidationResult with any errors or warnings.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check required files
        errors.extend(self._check_required_files(generated_files, self.REQUIRED_FILES))

        # Check non-empty
        for req_file in self.REQUIRED_FILES:
            errors.extend(self._check_non_empty(generated_files, req_file))

        # Validate Command.md content
        command_md = generated_files.get("Command.md", "")
        if command_md and command_md.strip():
            errors.extend(self._validate_command_md(command_md, manifest))

        # Validate command_config/template.json content
        config_content = generated_files.get("command_config/template.json", "")
        if config_content and config_content.strip():
            errors.extend(self._validate_command_config(config_content))

        # Warnings for missing optional sections
        if command_md:
            if "## Examples" not in command_md:
                warnings.append("Missing Examples section in Command.md")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_command_md(
        self,
        content: str,
        manifest: Dict[str, Any],
    ) -> List[str]:
        """Validate Command.md structure and content.

        Checks for a # heading matching the component name and a Usage section.

        Args:
            content: The Command.md file content.
            manifest: The manifest.json content.

        Returns:
            A list of error messages.
        """
        errors: List[str] = []

        # Get component name from manifest
        component_name = manifest.get("name", "")

        # Check for # heading matching component name
        has_heading = False
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                heading_name = stripped[2:].strip()
                if heading_name == component_name:
                    has_heading = True
                break  # Only check the first top-level heading

        if not has_heading and component_name:
            errors.append(
                f"Command.md is missing # heading matching component name '{component_name}'"
            )

        # Check for Usage section
        if "## Usage" not in content:
            errors.append("Command.md is missing required '## Usage' section")

        return errors

    def _validate_command_config(self, content: str) -> List[str]:
        """Validate command_config/template.json structure and content.

        Checks that the JSON is valid and contains name and description.

        Args:
            content: The command_config/template.json file content.

        Returns:
            A list of error messages.
        """
        errors: List[str] = []

        try:
            config = json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"command_config/template.json is not valid JSON: {e}")
            return errors

        if not isinstance(config, dict):
            errors.append("command_config/template.json root must be a JSON object")
            return errors

        # Check required fields
        required_fields = ["name", "description"]
        for field_name in required_fields:
            if field_name not in config:
                errors.append(
                    f"command_config/template.json is missing required field: '{field_name}'"
                )

        return errors
