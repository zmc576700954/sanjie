"""DocHub MCP server implementation."""

from __future__ import annotations

from typing import Any, Dict

from core.mcp_base.server import MCPServerBase

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool


class DocHubMCPServer(MCPServerBase):
    """MCP server that exposes DocHub document management and search tools."""

    def __init__(self, config: DocHubConfig) -> None:
        super().__init__(name="dochub", version="1.0.0")
        self.config = config
        self.register_tool(DocHubTool(config))

    def get_server_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": "DocHub team knowledge-base server",
            "config_path": str(self.config.base_path / "dochub.yaml"),
        }
