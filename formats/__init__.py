"""Format template definitions for all supported tools.

Provides template files and configuration schemas for generating
tool-specific format output from core components.

Supported tools:
    - claude: SKILL.md, plugin_config.json, slash commands
    - zcode: Command.md, command_config.json
    - cursor: SKILL.md, cursor_config.json
    - reasionix: Python script, deepseek_config.json
    - mcp: MCP server Python, mcp_config.json
"""

from __future__ import annotations

from pathlib import Path

FORMATS_DIR: Path = Path(__file__).parent

SUPPORTED_TOOLS: list[str] = ["claude", "zcode", "cursor", "reasionix", "mcp"]
