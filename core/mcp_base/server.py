"""MCP server base class -- defines the contract for MCP server components.

An MCP server registers ToolBase instances and provides list_tools / call_tool
operations for MCP protocol compliance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from core.shared.errors import AgentsDevelopError
from core.tools.base import ToolBase


class ToolNotFoundError(AgentsDevelopError):
    """Raised when a tool is not found on the MCP server."""


class MCPServerBase(ABC):
    """Base class for MCP server implementations.

    An MCP server maintains a registry of ToolBase instances and provides
    methods to list tool definitions and dispatch tool calls.

    Subclasses must implement:
        - get_server_info(): Return server metadata.
    """

    def __init__(self, name: str, version: str = "1.0.0") -> None:
        """Initialize the MCP server.

        Args:
            name: Server name identifier.
            version: Server version string.
        """
        self.name = name
        self.version = version
        self._tools: List[ToolBase] = []

    def register_tool(self, tool: ToolBase) -> None:
        """Register a tool with the MCP server.

        Args:
            tool: A ToolBase instance to register.
        """
        self._tools.append(tool)

    @abstractmethod
    def get_server_info(self) -> Dict[str, Any]:
        """Return server metadata.

        Returns:
            A dictionary with server information such as name, version,
            and capabilities.
        """

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tool function definitions registered on this server.

        Returns:
            A list of MCP-style function definition dictionaries aggregated
            from all registered tools.
        """
        all_defs: List[Dict[str, Any]] = []
        for tool in self._tools:
            all_defs.extend(tool.function_definitions)
        return all_defs

    def call_tool(self, tool_name: str, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a function on a registered tool.

        Args:
            tool_name: The name of the registered tool.
            function_name: The name of the function to invoke on the tool.
            arguments: Arguments to pass to the function.

        Returns:
            The function's return value.

        Raises:
            ToolNotFoundError: If no tool with the given name is registered.
        """
        for tool in self._tools:
            if tool.name == tool_name:
                return tool.run(function_name, arguments)
        raise ToolNotFoundError(f"Tool '{tool_name}' not found")
