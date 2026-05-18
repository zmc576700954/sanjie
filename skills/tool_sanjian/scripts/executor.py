"""Execute file write operations with backup and syntax validation."""
import os
import py_compile
from typing import Optional


def execute_write(filepath: str, content: str, operation: str = "REWRITE", backup: bool = True) -> dict:
    """
    Write content to file with backup and validation.

    Args:
        filepath: Target file path
        content: New file content
        operation: REWRITE / RESTRUCTURE / INTEGRATE
        backup: Whether to create backup

    Returns:
        {success, filepath, operation, backup_path, message}
    """
    backup_path: Optional[str] = None

    # Backup original
    if backup and os.path.exists(filepath):
        backup_path = filepath + ".sanjian_backup"
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)

    # Write new content
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # Validate syntax for Python files
    if filepath.endswith('.py'):
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            # Rollback on failure
            if backup_path and os.path.exists(backup_path):
                with open(filepath, 'w', encoding='utf-8') as f:
                    with open(backup_path, 'r', encoding='utf-8') as bk:
                        f.write(bk.read())
                os.remove(backup_path)
            return {
                "success": False,
                "filepath": filepath,
                "operation": operation,
                "backup_path": None,
                "message": f"Syntax validation failed, rolled back. Error: {e}",
            }

    return {
        "success": True,
        "filepath": filepath,
        "operation": operation,
        "backup_path": backup_path,
        "message": f"Write complete: {operation} -> {filepath}",
    }
