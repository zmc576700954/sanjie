"""MCP (Model Context Protocol) format validator.

Validates that generated MCP format files conform to the expected structure:
- mcp_server.py must be valid Python syntax with Server import and instantiation.
- mcp_config.json must be valid JSON with mcpServers field.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from migration.validators.base import FormatValidator, ValidationResult


class MCPFormatValidator(FormatValidator):
    """Validate generated MCP format files.

    Checks:
        - mcp_server.py exists and is non-empty.
        - mcp_server.py is valid Python syntax (uses ``compile()``).
        - mcp_server.py has a ``Server`` import and instantiation.
        - mcp_config.json exists and is valid JSON.
        - mcp_config.json has ``mcpServers`` field with correct structure.

    Warnings:
        - Missing ``async def main`` function in mcp_server.py.
    """

    tool_name = "mcp"

    REQUIRED_FILES: List[str] = ["mcp_server.py", "mcp_config.json"]

    def validate(
        self,
        generated_files: Dict[str, str],
        manifest: Dict[str, Any],
    ) -> ValidationResult:
        """Validate MCP format files.

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

        # Validate mcp_server.py content
        server_content = generated_files.get("mcp_server.py", "")
        if server_content and server_content.strip():
            server_errors, server_warnings = self._validate_server_py(server_content)
            errors.extend(server_errors)
            warnings.extend(server_warnings)

        # Validate mcp_config.json content
        config_content = generated_files.get("mcp_config.json", "")
        if config_content and config_content.strip():
            errors.extend(self._validate_mcp_config(config_content, manifest))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_server_py(
        self,
        content: str,
    ) -> tuple[list[str], list[str]]:
        """Validate mcp_server.py content.

        Checks Python syntax validity, Server import, and Server instantiation.

        Args:
            content: The mcp_server.py file content.

        Returns:
            A tuple of (errors, warnings).
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check Python syntax
        try:
            compile(content, "<mcp_server.py>", "exec")
        except SyntaxError as e:
            errors.append(f"mcp_server.py has invalid Python syntax: {e}")

        # Check for Server import
        if "Server" not in content or "from mcp" not in content:
            # Also check for the import statement pattern
            if "from mcp.server import Server" not in content and "import Server" not in content:
                errors.append("mcp_server.py is missing Server import from mcp.server")

        # Check for Server instantiation
        if "Server(" not in content:
            errors.append("mcp_server.py is missing Server instantiation")

        # Warning for missing async main
        if "async def main" not in content:
            warnings.append("mcp_server.py is missing async main function")

        return errors, warnings

    def _validate_mcp_config(
        self,
        content: str,
        manifest: Dict[str, Any],
    ) -> List[str]:
        """Validate mcp_config.json structure and content.

        Checks that the JSON is valid and contains mcpServers with the
        expected nested structure.

        Args:
            content: The mcp_config.json file content.
            manifest: The manifest.json content.

        Returns:
            A list of error messages.
        """
        errors: List[str] = []

        try:
            config = json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"mcp_config.json is not valid JSON: {e}")
            return errors

        if not isinstance(config, dict):
            errors.append("mcp_config.json root must be a JSON object")
            return errors

        # Check mcpServers field
        if "mcpServers" not in config:
            errors.append("mcp_config.json is missing required field: 'mcpServers'")
            return errors

        mcp_servers = config["mcpServers"]
        if not isinstance(mcp_servers, dict):
            errors.append("'mcpServers' field must be a JSON object")
            return errors

        # Check that mcpServers has at least one server entry
        if len(mcp_servers) == 0:
            errors.append("'mcpServers' field is empty -- must contain at least one server")
            return errors

        # Validate structure of each server entry
        for server_name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                errors.append(
                    f"mcpServers['{server_name}'] must be a JSON object"
                )
                continue

            # Each server entry should have at least a 'command' field
            if "command" not in server_config:
                errors.append(
                    f"mcpServers['{server_name}'] is missing 'command' field"
                )

        return errors
