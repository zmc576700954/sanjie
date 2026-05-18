"""File write with AST-level regression validation."""
import os
import ast
import py_compile

from skills.utils import ensure_safe_path


def write_with_validation(filepath: str, content: str, workspace_root: str = None) -> str:
    """
    Write file content with syntax and AST regression checks.
    Rolls back on failure.

    Args:
        filepath: Target file path
        content: New file content
        workspace_root: Optional workspace root for path validation

    Returns:
        Success or failure message string
    """
    if workspace_root is not None:
        filepath = ensure_safe_path(filepath, workspace_root)
    # Backup original
    original_content = None
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

    # Write
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # Validate Python files
    if filepath.endswith('.py'):
        try:
            py_compile.compile(filepath, doraise=True)

            tree = ast.parse(content)
            for node in ast.walk(tree):
                # Block dangerous module imports
                if isinstance(node, ast.ImportFrom) and node.module and "db_error_module" in node.module:
                    raise ValueError("Dangerous module import detected: db_error_module")
                # Block empty function implementations
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        raise ValueError(f"Empty function body detected: {node.name}")

        except (py_compile.PyCompileError, ValueError, SyntaxError) as e:
            # Rollback
            if original_content is not None:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                action = "Rolled back to original."
            else:
                os.remove(filepath)
                action = "Removed new file."
            return f"Error: Regression validation failed. {action} Detail: {e}"

    return f"Success: Write complete, passed validation."
