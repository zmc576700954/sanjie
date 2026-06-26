"""Claude Code/Desktop format validator.

Validates that generated Claude format files conform to the expected structure:
- SKILL.md must have YAML frontmatter with name field and an Instructions section.
- plugin_config.json must be valid JSON with name, version, description, and type.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from migration.validators.base import FormatValidator, ValidationResult


class ClaudeFormatValidator(FormatValidator):
    """Validate generated Claude format files.

    Checks:
        - SKILL.md exists and is non-empty.
        - SKILL.md has YAML frontmatter (``---`` delimiters) with a ``name`` field.
        - SKILL.md has an ``## Instructions`` section.
        - plugin_config.json exists and is valid JSON.
        - plugin_config.json has ``name``, ``version``, ``description``, and ``type`` fields.

    Warnings:
        - Missing ``## Examples`` section in SKILL.md.
        - Missing ``## Checklist`` section in SKILL.md.
    """

    tool_name = "claude"

    REQUIRED_FILES: List[str] = ["SKILL.md", "plugin_config.json"]

    def validate(
        self,
        generated_files: Dict[str, str],
        manifest: Dict[str, Any],
    ) -> ValidationResult:
        """Validate Claude format files.

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

        # Validate SKILL.md content
        skill_md = generated_files.get("SKILL.md", "")
        if skill_md and skill_md.strip():
            errors.extend(self._validate_skill_md(skill_md, manifest))

        # Validate plugin_config.json content
        config_content = generated_files.get("plugin_config.json", "")
        if config_content and config_content.strip():
            errors.extend(self._validate_plugin_config(config_content))

        # Warnings for missing optional sections
        if skill_md:
            if "## Examples" not in skill_md:
                warnings.append("Missing Examples section in SKILL.md")
            if "## Checklist" not in skill_md:
                warnings.append("Missing Checklist section in SKILL.md")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_skill_md(
        self,
        content: str,
        manifest: Dict[str, Any],
    ) -> List[str]:
        """Validate SKILL.md structure and content.

        Checks for YAML frontmatter with name field and Instructions section.

        Args:
            content: The SKILL.md file content.
            manifest: The manifest.json content.

        Returns:
            A list of error messages.
        """
        errors: List[str] = []

        # Check for YAML frontmatter
        if not content.startswith("---"):
            # Frontmatter might not be at the very start if there's whitespace
            stripped = content.lstrip()
            if not stripped.startswith("---"):
                errors.append("SKILL.md is missing YAML frontmatter (--- delimiters)")
                return errors

        # Extract frontmatter
        frontmatter_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            errors.append("SKILL.md has invalid YAML frontmatter (missing closing ---)")
            return errors

        frontmatter = frontmatter_match.group(1)

        # Check for name field in frontmatter
        if not re.search(r"^name\s*:", frontmatter, re.MULTILINE):
            errors.append("SKILL.md frontmatter is missing required 'name' field")

        # Check for Instructions section
        if "## Instructions" not in content:
            errors.append("SKILL.md is missing required '## Instructions' section")

        return errors

    def _validate_plugin_config(self, content: str) -> List[str]:
        """Validate plugin_config.json structure and content.

        Checks that the JSON is valid and contains required fields.

        Args:
            content: The plugin_config.json file content.

        Returns:
            A list of error messages.
        """
        errors: List[str] = []

        try:
            config = json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"plugin_config.json is not valid JSON: {e}")
            return errors

        if not isinstance(config, dict):
            errors.append("plugin_config.json root must be a JSON object")
            return errors

        # Check required fields
        required_fields = ["name", "version", "description", "type"]
        for field_name in required_fields:
            if field_name not in config:
                errors.append(f"plugin_config.json is missing required field: '{field_name}'")

        return errors
