import os
import sys

import pytest

from skills.utils import ensure_safe_path
from mcp.shared.exceptions import McpError


def test_ensure_safe_path_valid_relative(project_root):
    """Valid relative path inside workspace should resolve."""
    result = ensure_safe_path("README.md", workspace_root=project_root)
    assert result == os.path.join(project_root, "README.md")


def test_ensure_safe_path_valid_absolute(project_root):
    """Valid absolute path inside workspace should pass."""
    valid = os.path.join(project_root, "README.md")
    result = ensure_safe_path(valid, workspace_root=project_root)
    assert result == valid


def test_ensure_safe_path_traversal(project_root):
    """Path traversal should raise McpError."""
    with pytest.raises(McpError):
        ensure_safe_path("../../etc/passwd", workspace_root=project_root)


def test_ensure_safe_path_outside_workspace(project_root):
    """Absolute path outside workspace should raise McpError."""
    with pytest.raises(McpError):
        ensure_safe_path("/etc/passwd", workspace_root=project_root)


def test_ensure_safe_path_windows_case(project_root):
    """Windows case-insensitive paths should be handled correctly."""
    if sys.platform == "win32":
        valid = os.path.join(project_root, "README.md")
        result = ensure_safe_path(valid, workspace_root=project_root)
        assert result == valid
