"""Tool base class -- defines the contract for all tool components.

A tool is a component that exposes one or more callable functions with
well-defined input schemas, suitable for MCP integration.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, CoreComponent


class ToolBase(CoreComponent):
    """Base class for tool components.

    Tools expose function definitions (in MCP tool format) and implement
    a ``run()`` method that dispatches to the appropriate function.

    Subclasses must implement:
        - function_definitions: List of MCP-style function definitions.
        - run(): Execute a named function with given arguments.
    """

    def __init__(self, metadata: ComponentMetadata) -> None:
        super().__init__(metadata)
        self._function_defs: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def function_definitions(self) -> List[Dict[str, Any]]:
        """Return the list of tool function definitions in MCP tool format.

        Each definition is a dictionary with at least ``"name"``,
        ``"description"``, and ``"inputSchema"`` keys.
        """

    @abstractmethod
    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a named tool function with the given arguments.

        Args:
            function_name: The name of the function to invoke.
            arguments: The arguments to pass to the function.

        Returns:
            The function's return value.
        """

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function by dispatching to ``run()``.

        Extracts ``"function"`` and ``"arguments"`` from *input_data* and
        delegates to ``run()``.

        Args:
            input_data: Must contain ``"function"`` (str) and optionally
                        ``"arguments"`` (dict).

        Returns:
            Dictionary with ``"function"`` and ``"result"`` keys.
        """
        func_name = input_data.get("function", "")
        args = input_data.get("arguments", {})
        result = self.run(func_name, args)
        return {"function": func_name, "result": result}
