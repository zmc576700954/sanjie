"""Precision text replacement with regression validation."""
import os
import sys
import py_compile

from skills.utils import ensure_safe_path

# Maximum file size for in-memory replacement (100 MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def precise_replace(filepath: str, old_str: str, new_str: str, workspace_root: str | None = None) -> str:
    """
    Replace exact text in file with validation and rollback.

    Replaces only the FIRST occurrence of old_str (via str.replace(old, new, 1)).

    Args:
        filepath: Target file path
        old_str: Exact text to find and replace (must be non-empty string)
        new_str: Replacement text (can be empty for deletion)
        workspace_root: Optional workspace root for path validation

    Returns:
        Success or failure message string
    """
    # -- Type guards --
    if not isinstance(filepath, str):
        return f"Error: filepath must be a string, got {type(filepath).__name__}."
    if not isinstance(old_str, str):
        return f"Error: old_str must be a string, got {type(old_str).__name__}."
    if not isinstance(new_str, str):
        return f"Error: new_str must be a string, got {type(new_str).__name__}."
    if not old_str:
        return "Error: old_str cannot be empty."

    # -- Path validation --
    try:
        filepath = ensure_safe_path(filepath, workspace_root)
    except Exception as e:
        return f"Error: Path validation failed - {e}"

    if not os.path.exists(filepath):
        return f"Error: File {filepath} not found."
    if os.path.isdir(filepath):
        return f"Error: {filepath} is a directory, not a file."

    # -- File size guard --
    try:
        file_size = os.path.getsize(filepath)
    except OSError as e:
        return f"Error: Cannot read file size - {e}"
    if file_size > MAX_FILE_SIZE:
        return (
            f"Error: File too large ({file_size / 1024 / 1024:.1f} MB). "
            f"Limit is {MAX_FILE_SIZE / 1024 / 1024:.0f} MB."
        )

    # -- Read file --
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return f"Error: File {filepath} is not valid UTF-8 text."

    if old_str not in content:
        return f"Error: Target string not found in {filepath}. Aborting."

    # -- Replace (single occurrence) --
    new_content = content.replace(old_str, new_str, 1)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except OSError as e:
        return f"Error: Failed to write file - {e}"

    # -- Validate: confirm write --
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            verified = f.read()
    except OSError as e:
        _rollback(filepath, content)
        return f"Error: Write verification read failed - {e}. Rolled back."

    # new_str must be present in the result
    if new_str not in verified:
        _rollback(filepath, content)
        return "Error: Write verification failed - new_str absent after write. Rolled back."

    # The file content must have changed (unless old_str == new_str, i.e. idempotent).
    # We do NOT check that old_str is completely gone from the file, because
    # str.replace(old, new, 1) only replaces the FIRST occurrence; remaining
    # occurrences are expected to stay.
    if old_str != new_str and verified == content:
        _rollback(filepath, content)
        return "Error: Write verification failed - file content unchanged after replace. Rolled back."

    # -- Validate: syntax check for Python --
    if filepath.endswith('.py'):
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            _rollback(filepath, content)
            return f"Error: Syntax check failed, rolled back. {e}"

    # -- Audit log (to stderr for MCP context) --
    _audit_log(filepath, old_str, new_str, file_size)

    return f"Success: Replaced text in {filepath}, passed validation."


def _rollback(filepath: str, original_content: str) -> None:
    """Restore file to original content. Best-effort, ignores write errors."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(original_content)
    except OSError:
        pass


def _audit_log(filepath: str, old_str: str, new_str: str, original_size: int) -> None:
    """Optional audit log to stderr for traceability."""
    try:
        old_preview = repr(old_str[:60]) if len(old_str) > 60 else repr(old_str)
        new_preview = repr(new_str[:60]) if len(new_str) > 60 else repr(new_str)
        print(
            f"[yindan] replace in {filepath} | "
            f"old={old_preview} -> new={new_preview} | "
            f"file_size={original_size}",
            file=sys.stderr,
        )
    except Exception:
        pass  # Never let audit logging break the main operation
