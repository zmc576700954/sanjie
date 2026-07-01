from __future__ import annotations

import asyncio
import os
from pathlib import Path

from skill_manager.builtin_skills import load_builtin_skills
from skill_manager.server import create_server
from skill_manager.store import FileSystemStore


DEFAULT_ROOT = Path.home() / ".agents-develop" / "skill-manager"


def main() -> None:
    root = os.environ.get("SKILL_MANAGER_ROOT", str(DEFAULT_ROOT))
    store = FileSystemStore(root)
    load_builtin_skills(store)

    server = create_server(store)

    async def run() -> None:
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
