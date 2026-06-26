"""Format validator base class -- defines the contract for all format validators.

Each validator checks that generated format files conform to the structural
and content requirements of a specific target tool. Validators return a
ValidationResult with errors (must-fix) and warnings (should-fix).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    """Result of validating generated format files.

    Attributes:
        valid: True if no errors were found (warnings do not affect validity).
        errors: List of error messages (must-fix issues).
        warnings: List of warning messages (should-fix issues).
    """

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FormatValidator(ABC):
    """Abstract base class for format validators.

    Subclasses must:
        - Set the ``tool_name`` class attribute (e.g. "claude", "zcode").
        - Implement ``validate()`` to check generated files against tool specs.

    The base class provides helper methods for common validation patterns:
        - ``_check_required_files()``: Verify that all required files are present.
        - ``_check_non_empty()``: Verify that a file is not empty.
    """

    tool_name: str = ""

    @abstractmethod
    def validate(
        self,
        generated_files: Dict[str, str],
        manifest: Dict[str, Any],
    ) -> ValidationResult:
        """Validate generated format files against tool specifications.

        Args:
            generated_files: A dictionary mapping relative file paths to
                             generated file content.
            manifest: The manifest.json content providing component metadata.

        Returns:
            A ValidationResult with any errors or warnings found.
        """

    def _check_required_files(
        self,
        generated_files: Dict[str, str],
        required: List[str],
    ) -> List[str]:
        """Check that all required files are present in the generated output.

        Args:
            generated_files: The generated file content mapping.
            required: List of required file paths.

        Returns:
            A list of error messages for any missing files.
        """
        errors: List[str] = []
        for req in required:
            if req not in generated_files:
                errors.append(f"Missing required file: {req}")
        return errors

    def _check_non_empty(
        self,
        generated_files: Dict[str, str],
        file_path: str,
    ) -> List[str]:
        """Check that a file is not empty in the generated output.

        Args:
            generated_files: The generated file content mapping.
            file_path: The file path to check.

        Returns:
            A list of error messages (empty if the file has content).
        """
        errors: List[str] = []
        content = generated_files.get(file_path, "")
        if not content or not content.strip():
            errors.append(f"File is empty: {file_path}")
        return errors
