"""MCP tool definition dataclass.

Provides a structured way to define MCP tool functions with name,
description, and inputSchema, and to convert them to the MCP wire format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MCPToolDefinition:
    """Dataclass representing an MCP tool definition.

    Attributes:
        name: The tool function name.
        description: Human-readable description of what the tool does.
        inputSchema: JSON Schema describing the tool's input parameters.
    """

    name: str
    description: str = ""
    inputSchema: Dict[str, Any] = field(default_factory=dict)

    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert this definition to the MCP wire-format dictionary.

        Returns:
            A dictionary with ``"name"``, ``"description"``, and
            ``"inputSchema"`` keys suitable for MCP protocol responses.
        """
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema,
        }
