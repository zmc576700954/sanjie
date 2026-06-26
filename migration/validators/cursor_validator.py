"""Cursor format validator.

Validates that generated Cursor format files conform to the expected structure:
- SKILL.md must have YAML frontmatter with cursorVersion field.
- cursor_config.json must be valid JSON with skills and mcpServers fields.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from migration.validators.base import FormatValidator, ValidationResult


class CursorFormatValidator(FormatValidator):
    """Validate generated Cursor format files.

    Checks:
        - SKILL.md exists and is non-empty.
        - SKILL.md has YAML frontmatter.
        - cursor_config.json exists and is valid JSON.
        - cursor_config.json has ``skills`` and ``mcpServers`` fields.

    Warnings:
        - Missing ``cursorVersion`` in SKILL.md frontmatter.
    """

    tool_name = "cursor"

    REQUIRED_FILES: List[str] = ["SKILL.md", "cursor_config.json"]

    def validate(
        self,
        generated_files: Dict[str, str],
        manifest: Dict[str, Any],
    ) -> ValidationResult:
        """Validate Cursor format files.

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
            md_errors, md_warnings = self._validate_skill_md(skill_md)
            errors.extend(md_errors)
            warnings.extend(md_warnings)

        # Validate cursor_config.json content
        config_content = generated_files.get("cursor_config.json", "")
        if config_content and config_content.strip():
            errors.extend(self._validate_cursor_config(config_content))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_skill_md(
        self,
        content: str,
    ) -> tuple[list[str], list[str]]:
        """Validate SKILL.md structure and content.

        Checks for YAML frontmatter. Warns if cursorVersion is missing.

        Args:
            content: The SKILL.md file content.

        Returns:
            A tuple of (errors, warnings).
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check for YAML frontmatter
        stripped = content.lstrip()
        if not stripped.startswith("---"):
            errors.append("SKILL.md is missing YAML frontmatter (--- delimiters)")
            return errors, warnings

        # Extract frontmatter
        frontmatter_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            errors.append("SKILL.md has invalid YAML frontmatter (missing closing ---)")
            return errors, warnings

        frontmatter = frontmatter_match.group(1)

        # Warn if cursorVersion is missing
        if not re.search(r"^cursorVersion\s*:", frontmatter, re.MULTILINE):
            warnings.append("SKILL.md frontmatter is missing 'cursorVersion' field")

        return errors, warnings

    def _validate_cursor_config(self, content: str) -> List[str]:
        """Validate cursor_config.json structure and content.

        Checks that the JSON is valid and contains skills and mcpServers.

        Args:
            content: The cursor_config.json file content.

        Returns:
            A list of error messages.
        """
        errors: List[str] = []

        try:
            config = json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"cursor_config.json is not valid JSON: {e}")
            return errors

        if not isinstance(config, dict):
            errors.append("cursor_config.json root must be a JSON object")
            return errors

        # Check required fields
        required_fields = ["skills", "mcpServers"]
        for field_name in required_fields:
            if field_name not in config:
                errors.append(f"cursor_config.json is missing required field: '{field_name}'")

        return errors
