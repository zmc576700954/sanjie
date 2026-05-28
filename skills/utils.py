import os
import threading
import tempfile

try:
    from mcp.shared.exceptions import McpError
    from mcp.types import ErrorData, INVALID_PARAMS
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False

# -- Concurrency-safe file writing --

_file_locks: dict[str, threading.Lock] = {}
_lock_registry_mutex = threading.Lock()


def _get_file_lock(filepath: str) -> threading.Lock:
    abs_path = os.path.abspath(filepath)
    with _lock_registry_mutex:
        if abs_path not in _file_locks:
            _file_locks[abs_path] = threading.Lock()
        return _file_locks[abs_path]


def atomic_append(filepath: str, content: str, encoding: str = "utf-8") -> None:
    lock = _get_file_lock(filepath)
    with lock:
        with open(filepath, "a", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())


def atomic_write(filepath: str, content: str, encoding: str = "utf-8") -> None:
    dir_name = os.path.dirname(filepath) or "."
    lock = _get_file_lock(filepath)
    with lock:
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, filepath)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def ensure_safe_path(filepath: str, workspace_root: str | None = None) -> str:
    """Resolves the absolute path and ensures it lies within the workspace root."""
    if not isinstance(filepath, str):
        raise McpError(
            ErrorData(code=INVALID_PARAMS, message=f"Path must be a string, got {type(filepath).__name__}")
        )

    if "\x00" in filepath:
        raise McpError(
            ErrorData(code=INVALID_PARAMS, message="Null byte detected in path -- possible injection attempt")
        )

    if not filepath:
        raise McpError(
            ErrorData(code=INVALID_PARAMS, message="Empty filepath is not allowed")
        )

    if not workspace_root:
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    abs_path = os.path.abspath(filepath)
    abs_root = os.path.abspath(workspace_root)

    try:
        if not os.path.commonpath([abs_path, abs_root]) == abs_root:
            raise McpError(
                ErrorData(code=INVALID_PARAMS, message=f"Path traversal detected or path outside workspace: {filepath}")
            )
    except ValueError:
        raise McpError(
            ErrorData(code=INVALID_PARAMS, message=f"Path traversal detected or path outside workspace: {filepath}")
        )
    return abs_path
