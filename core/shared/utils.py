"""Common utility functions for agents_develop.

Provides helpers for string conversion, version validation, manifest I/O,
and directory creation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict


def snake_case(text: str) -> str:
    """Convert a string to snake_case.

    Handles CamelCase, kebab-case, and space-separated words.

    Args:
        text: The input string to convert.

    Returns:
        The snake_case version of the input.

    Examples:
        >>> snake_case("MyComponent")
        'my_component'
        >>> snake_case("some-kebab-name")
        'some_kebab_name'
        >>> snake_case("Already snake_case")
        'already_snake_case'
    """
    # Replace hyphens and spaces with underscores
    text = text.replace("-", "_").replace(" ", "_")
    # Insert underscore before an uppercase letter that follows a lowercase letter or digit
    text = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", text)
    # Insert underscore between consecutive uppercase letters followed by a lowercase letter
    # e.g. "XMLParser" -> "XML_Parser" before lowercasing
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    # Lowercase everything
    return text.lower()


def validate_version(version: str) -> bool:
    """Validate that a version string follows semantic versioning.

    Accepts strings matching the pattern MAJOR.MINOR.PATCH where each
    component is a non-negative integer. Pre-release suffixes (e.g. ``-alpha``)
    are not supported in this simplified check.

    Args:
        version: The version string to validate.

    Returns:
        True if the version is valid semver, False otherwise.

    Examples:
        >>> validate_version("1.0.0")
        True
        >>> validate_version("0.1.0")
        True
        >>> validate_version("1.0")
        False
        >>> validate_version("v1.0.0")
        False
    """
    pattern = r"^\d+\.\d+\.\d+$"
    return bool(re.match(pattern, version))


def load_manifest(path: Path) -> Dict[str, Any]:
    """Load a manifest.json file and return its contents as a dictionary.

    Args:
        path: Path to the manifest.json file.

    Returns:
        The parsed JSON content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def save_manifest(path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary as a manifest.json file.

    Creates parent directories if they do not exist.

    Args:
        path: Path to write the manifest.json file.
        data: The dictionary to serialize as JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")


def ensure_dir(path: Path) -> None:
    """Create a directory (and parents) if it does not already exist.

    Args:
        path: The directory path to create.
    """
    path.mkdir(parents=True, exist_ok=True)
