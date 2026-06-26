"""Unified error hierarchy for agents_develop.

All custom exceptions inherit from AgentsDevelopError, organized by domain:
- ComponentError: Issues with component registration, lookup, or validation
- MigrationError: Issues with format generation, validation, or tool support
- ConfigError: Issues with configuration management
"""

from __future__ import annotations


class AgentsDevelopError(Exception):
    """Base error for all agents_develop errors."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(self.message)


# ── Component Errors ──────────────────────────────────────────────────────────


class ComponentError(AgentsDevelopError):
    """Base error for component-related issues."""


class ComponentNotFoundError(ComponentError):
    """Raised when a component is not found in the registry."""


class DuplicateComponentError(ComponentError):
    """Raised when attempting to register a component that already exists."""


class ComponentValidationError(ComponentError):
    """Raised when component input or output fails validation."""


# ── Migration Errors ──────────────────────────────────────────────────────────


class MigrationError(AgentsDevelopError):
    """Base error for migration-related issues."""


class FormatGenerationError(MigrationError):
    """Raised when format generation fails for a target tool."""


class FormatValidationError(MigrationError):
    """Raised when generated format output fails validation."""


class UnsupportedToolError(MigrationError):
    """Raised when a target tool is not supported."""

    def __init__(self, tool_name: str = "") -> None:
        self.tool_name = tool_name
        message = f"Unsupported tool: '{tool_name}'" if tool_name else "Unsupported tool"
        super().__init__(message)


class TemplateError(MigrationError):
    """Raised when template rendering fails."""


# ── Config Errors ─────────────────────────────────────────────────────────────


class ConfigError(AgentsDevelopError):
    """Raised when there is a configuration error."""
