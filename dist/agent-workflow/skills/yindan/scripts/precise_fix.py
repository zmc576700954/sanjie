"""Precision text replacement with regression validation."""
import os
import py_compile


def precise_replace(filepath: str, old_str: str, new_str: str) -> str:
    """
    Replace exact text in file with validation and rollback.

    Args:
        filepath: Target file path
        old_str: Exact text to find and replace
        new_str: Replacement text

    Returns:
        Success or failure message string
    """
    if not os.path.exists(filepath):
        return f"Error: File {filepath} not found."

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if old_str not in content:
        return f"Error: Target string not found in {filepath}. Aborting."

    new_content = content.replace(old_str, new_str, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Validate: confirm write
    with open(filepath, 'r', encoding='utf-8') as f:
        verified = f.read()
        if new_str not in verified:
            return f"Error: Write verification failed."

    # Validate: syntax check for Python
    if filepath.endswith('.py'):
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Error: Syntax check failed, rolled back. {e}"

    return f"Success: Replaced text in {filepath}, passed validation."
