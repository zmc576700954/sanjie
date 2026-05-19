import os
import sys

import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Allow direct import of auto_server from mcp-servers directory
mcp_servers_dir = os.path.join(project_root, "mcp-servers")
if mcp_servers_dir not in sys.path:
    sys.path.insert(0, mcp_servers_dir)


@pytest.fixture
def project_root() -> str:
    """Return the absolute path to the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
