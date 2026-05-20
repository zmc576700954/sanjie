"""File write with AST-level regression validation."""
import os
import ast
import py_compile

from skills.utils import ensure_safe_path


def write_with_validation(filepath: str, content: str, workspace_root: str | None = None) -> str:
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

            # Step 1: collect imported names from dangerous modules
            # Maps local_name -> set of dangerous function names
            DANGEROUS_MODULES = {
                "os": {"system", "popen", "startfile"},
                "subprocess": {"run", "Popen", "call", "check_output", "check_call", "getoutput", "getstatusoutput"},
            }
            DANGEROUS_BUILTINS = {"eval", "exec"}

            dangerous_imports: dict[str, set[str]] = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in DANGEROUS_MODULES:
                            local_name = alias.asname or alias.name
                            dangerous_imports[local_name] = DANGEROUS_MODULES[alias.name]
                elif isinstance(node, ast.ImportFrom) and node.module in DANGEROUS_MODULES:
                    for alias in node.names:
                        if alias.name in DANGEROUS_MODULES[node.module]:
                            local_name = alias.asname or alias.name
                            dangerous_imports.setdefault(local_name, set()).add(alias.name)

            # Step 2: check actual calls for dangerous operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        # Pattern: os.system(...) or subprocess.run(...)
                        if isinstance(node.func.value, ast.Name):
                            mod = node.func.value.id
                            func = node.func.attr
                            if mod in dangerous_imports and func in dangerous_imports[mod]:
                                raise ValueError(f"Dangerous call detected: {mod}.{func}")
                    elif isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in DANGEROUS_BUILTINS:
                            raise ValueError(f"Dangerous call detected: {func_name}")
                        if func_name in dangerous_imports:
                            raise ValueError(f"Dangerous call detected: {func_name}")

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
