"""MCP (Model Context Protocol) format generator.

Generates MCP server Python files and mcp_config.json from core components
for universal MCP integration across all tools.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from core.shared.base import CoreComponent
from core.tools.base import ToolBase
from core.mcp_base.tool_def import MCPToolDefinition
from migration.generators.base import FormatGenerator


class MCPFormatGenerator(FormatGenerator):
    """Generate MCP format files from a core component.

    Produces:
        - ``mcp_server.py.template``: MCP server Python file with tool
          definitions and handlers.
        - ``mcp_config.json``: MCP server configuration for tool integration.
    """

    tool_name = "mcp"

    def generate(self, component: CoreComponent, manifest: Dict[str, Any]) -> Dict[str, str]:
        """Generate MCP format files from a core component.

        Args:
            component: The core component (typically ToolBase).
            manifest: The manifest.json content.

        Returns:
            A dictionary mapping relative file paths to generated content.
            Keys include ``"mcp_server.py"`` and ``"mcp_config.json"``.
        """
        variables = self._extract_variables(component, manifest)
        output: Dict[str, str] = {}

        # Generate MCP server Python file
        server_vars = self._build_server_variables(variables, component, manifest)
        server_content = self._render_template("mcp_server.py", server_vars)
        output["mcp_server.py"] = server_content

        # Generate mcp_config.json
        config_vars = self._build_config_variables(variables, manifest)
        mcp_config = self._render_template("mcp_config.json", config_vars)
        output["mcp_config.json"] = mcp_config

        return output

    def _extract_variables(
        self,
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract variables with MCP-specific enhancements.

        Converts tool function_definitions to MCP tool definitions and handlers.
        """
        variables = super()._extract_variables(component, manifest)

        if isinstance(component, ToolBase):
            variables["tool_definitions"] = self._generate_tool_definitions(
                component.function_definitions
            )
            variables["tool_handlers"] = self._generate_tool_handlers(
                component.function_definitions
            )
        else:
            variables["tool_definitions"] = "# No tool definitions"
            variables["tool_handlers"] = "# No tool handlers"

        return variables

    @staticmethod
    def _generate_tool_definitions(function_defs: List[Dict[str, Any]]) -> str:
        """Generate MCP tool definition Python code from function_definitions.

        Creates ``@server.tool()`` decorated functions that register each
        tool with the MCP server.

        Args:
            function_defs: A list of MCP-style function definition dictionaries.

        Returns:
            Python code string defining the MCP tools.
        """
        if not function_defs:
            return "# No tool definitions"

        lines: List[str] = []
        for func_def in function_defs:
            name = func_def.get("name", "unnamed")
            description = func_def.get("description", "")
            input_schema = func_def.get("inputSchema", {})

            # Generate the @server.tool decorator and function
            lines.append(f"@server.tool()")
            lines.append(f"async def {name}(**kwargs):")
            lines.append(f'    """{description}"""')
            lines.append(f"    # TODO: Implement {name} logic")
            lines.append(f"    return {{'status': 'not_implemented', 'function': '{name}'}}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _generate_tool_handlers(function_defs: List[Dict[str, Any]]) -> str:
        """Generate MCP tool handler registration code.

        Creates the server tool list handler that returns all available tools.

        Args:
            function_defs: A list of MCP-style function definition dictionaries.

        Returns:
            Python code string for the tool list handler.
        """
        if not function_defs:
            return "# No tool handlers"

        tool_items: List[str] = []
        for func_def in function_defs:
            name = func_def.get("name", "unnamed")
            description = func_def.get("description", "")
            input_schema = json.dumps(func_def.get("inputSchema", {}), indent=4)
            # Indent the inputSchema for embedding in the function
            indented_schema = "\n".join(
                "            " + line for line in input_schema.split("\n")
            )
            tool_items.append(
                f'        Tool(name="{name}", description="{description}",\n'
                f"            inputSchema={indented_schema}),"
            )

        handler_code = "@server.list_tools()\n"
        handler_code += "async def list_tools():\n"
        handler_code += '    """List all available tools."""\n'
        handler_code += "    return [\n"
        handler_code += "\n".join(tool_items)
        handler_code += "\n    ]"

        return handler_code

    def _build_server_variables(
        self,
        variables: Dict[str, Any],
        component: CoreComponent,
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build variables for the mcp_server.py template."""
        return {
            "name": variables["name"],
            "description": variables["description"],
            "tool_definitions": variables.get("tool_definitions", "# No tool definitions"),
            "tool_handlers": variables.get("tool_handlers", "# No tool handlers"),
        }

    def _build_config_variables(
        self,
        variables: Dict[str, Any],
        manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build variables for the mcp_config.json template."""
        mcp_config = manifest.get("mcp_config", {})
        transport = mcp_config.get("transport", "stdio")

        return {
            "name": variables["name"],
            "mcp_transport": transport,
        }
