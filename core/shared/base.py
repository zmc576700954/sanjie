"""Core base classes for all components in agents_develop.

Defines the fundamental contracts that every component type must follow:
- ComponentType: Enum of supported component categories
- ComponentMetadata: Dataclass holding component metadata (maps to manifest.json)
- CoreComponent: Abstract base class for all components
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ComponentType(Enum):
    """Supported component types."""

    AGENT = "agent"
    SKILL = "skill"
    TOOL = "tool"
    MCP_SERVER = "mcp_server"


@dataclass
class ComponentMetadata:
    """Component metadata -- corresponds to manifest.json fields.

    Attributes:
        name: Component identifier in snake_case.
        type: The component type (agent, skill, tool, mcp_server).
        version: Semantic version string (e.g. "1.0.0").
        description: One-line description of the component.
        author: Author name.
        created: Creation date in YYYY-MM-DD format.
        updated: Last update date in YYYY-MM-DD format.
        tags: Searchable tags for the component.
        core_dependencies: Python package dependencies.
        supported_tools: Target tools this component supports.
        config_schema: JSON Schema for component configuration.
    """

    name: str
    type: ComponentType
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    created: str = ""
    updated: str = ""
    tags: List[str] = field(default_factory=list)
    core_dependencies: List[str] = field(default_factory=list)
    supported_tools: List[str] = field(
        default_factory=lambda: ["claude", "zcode", "cursor", "reasionix", "mcp"]
    )
    config_schema: Dict[str, Any] = field(default_factory=dict)


class CoreComponent(ABC):
    """Abstract base class for all core components.

    Every component (agent, skill, tool, MCP server) must inherit from this
    class and implement the abstract methods. The class provides a common
    interface for metadata access, configuration, serialization, and execution.
    """

    def __init__(self, metadata: ComponentMetadata) -> None:
        self._metadata = metadata
        self._config: Dict[str, Any] = {}

    @property
    def metadata(self) -> ComponentMetadata:
        """Return the component's metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Return the component's name."""
        return self._metadata.name

    @property
    def component_type(self) -> ComponentType:
        """Return the component's type."""
        return self._metadata.type

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the component's core logic.

        Args:
            input_data: Dictionary of input parameters for the component.

        Returns:
            Dictionary containing the execution results.
        """

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data meets the component's requirements.

        Args:
            input_data: Dictionary of input parameters to validate.

        Returns:
            True if the input is valid, False otherwise.
        """

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component with runtime settings.

        Args:
            config: Dictionary of configuration key-value pairs.
        """
        self._config = config

    def get_config_schema(self) -> Dict[str, Any]:
        """Return the JSON Schema for this component's configuration."""
        return self._metadata.config_schema

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the component to a dictionary for format generators.

        Returns:
            Dictionary with name, type, version, description, and config_schema.
        """
        return {
            "name": self.name,
            "type": self.component_type.value,
            "version": self._metadata.version,
            "description": self._metadata.description,
            "config_schema": self._metadata.config_schema,
        }
