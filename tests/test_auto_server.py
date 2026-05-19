"""Integration tests for the auto-discovery MCP server."""

import os

import pytest

from mcp.shared.exceptions import McpError

import auto_server
from skills.celestial_registry.skill_manifest import (
    MANIFEST_TO_PY_TYPE,
    MANIFEST_TO_PY_TYPE_STR,
)


class TestHasManualServer:
    def test_tianyan_has_manual_server(self):
        assert auto_server._has_manual_server("tianyan") is True

    def test_taibai_has_manual_server(self):
        assert auto_server._has_manual_server("taibai") is True

    def test_nonexistent_skill_no_manual_server(self):
        assert auto_server._has_manual_server("nonexistent_xyz") is False


class TestResolveScriptFunction:
    def test_resolve_logic_tracer(self):
        tool = {
            "name": "logic_tracer",
            "script": "scripts/logic_tracer.py",
        }
        func = auto_server._resolve_script_function("tool_tianyan", tool)
        assert func is not None
        assert callable(func)

    def test_resolve_unknown_module_returns_none(self):
        tool = {
            "name": "unknown_tool",
            "script": "scripts/nonexistent.py",
        }
        func = auto_server._resolve_script_function("tool_tianyan", tool)
        assert func is None


class TestLooksLikePath:
    def test_path_suffixes_detected(self):
        assert auto_server._looks_like_path("filepath") is True
        assert auto_server._looks_like_path("source_path") is True
        assert auto_server._looks_like_path("log_dir") is True

    def test_non_path_names_not_detected(self):
        assert auto_server._looks_like_path("file_type") is False
        assert auto_server._looks_like_path("directory_count") is False
        assert auto_server._looks_like_path("content") is False


class TestBuildToolWrapper:
    def test_wrapper_signature_includes_types(self):
        def dummy_func(error_desc: str, max_retries: int = 3) -> str:
            return f"{error_desc}:{max_retries}"

        tool = {
            "name": "dummy_tool",
            "parameters": {
                "error_desc": {"description": "Error text", "type": "string"},
                "max_retries": {"description": "Max retries", "type": "integer"},
            },
        }
        wrapper = auto_server._build_tool_wrapper("test_skill", tool, dummy_func)
        sig = wrapper.__signature__
        assert "error_desc" in sig.parameters
        assert "max_retries" in sig.parameters
        # Integer type should map to Python int annotation
        assert sig.parameters["max_retries"].annotation == int
        assert sig.parameters["error_desc"].annotation == str

    def test_wrapper_applies_path_safety(self):
        def dummy_func(filepath: str) -> str:
            return "ok"

        tool = {
            "name": "dummy_tool",
            "parameters": {
                "filepath": {"description": "Target file", "type": "path"},
            },
        }
        wrapper = auto_server._build_tool_wrapper("test_skill", tool, dummy_func)
        # Path traversal should be caught by ensure_safe_path
        with pytest.raises(McpError):
            wrapper(filepath="../../etc/passwd")


def test_manifest_type_map_consistency():
    """MANIFEST_TO_PY_TYPE and MANIFEST_TO_PY_TYPE_STR must have identical keys."""
    assert set(MANIFEST_TO_PY_TYPE.keys()) == set(MANIFEST_TO_PY_TYPE_STR.keys())
    for key, py_type in MANIFEST_TO_PY_TYPE.items():
        assert MANIFEST_TO_PY_TYPE_STR[key] == py_type.__name__
