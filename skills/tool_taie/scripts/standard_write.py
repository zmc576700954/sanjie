"""
File write with AST-level regression validation.
v2 — fixes all 8 confirmed defects and implements all 10 optimization items.
"""
import os
import ast
import logging
import py_compile
from datetime import datetime, timezone
from typing import Any

from skills.utils import ensure_safe_path
from skills.tool_taie.scripts.security_config import (
    DANGEROUS_MODULES,
    DANGEROUS_BUILTINS,
    DANGEROUS_BUILTIN_NAMES,
    TREAT_ELLIPSIS_AS_EMPTY,
    PYTHON_EXTENSIONS,
)

logger = logging.getLogger(__name__)

_audit_log: list[dict[str, Any]] = []


def get_audit_log() -> list[dict[str, Any]]:
    return list(_audit_log)


def _record_audit(filepath: str, success: bool, message: str) -> None:
    _audit_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "filepath": filepath,
        "success": success,
        "message": message,
    })
    if success:
        logger.info("WRITE OK: %s -- %s", filepath, message)
    else:
        logger.warning("WRITE FAIL: %s -- %s", filepath, message)


def _is_python_file(filepath: str) -> bool:
    _, ext = os.path.splitext(filepath)
    return ext.lower() in PYTHON_EXTENSIONS


def _is_empty_function_body(body: list) -> bool:
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is ...):
            continue
        return False
    return True


def _check_dangerous_calls(tree: ast.AST) -> str | None:
    alias_map: dict[str, str] = {}
    from_imports: dict[str, tuple[str, str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in DANGEROUS_MODULES:
                    local = alias.asname or alias.name
                    alias_map[local] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module in DANGEROUS_MODULES:
            mod = node.module
            for alias in node.names:
                if alias.name in DANGEROUS_MODULES[mod]:
                    local = alias.asname or alias.name
                    from_imports[local] = (mod, alias.name)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func

        # 2a. Direct attribute call: obj.method()
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            obj = func.value.id
            method = func.attr
            mod = alias_map.get(obj)
            if mod and method in DANGEROUS_MODULES.get(mod, set()):
                return f"Dangerous call detected: {mod}.{method} (via alias '{obj}')"

        # 2b. From-import direct call / builtin call
        if isinstance(func, ast.Name):
            name = func.id
            if name in DANGEROUS_BUILTINS:
                return f"Dangerous builtin call detected: {name}()"
            if name in from_imports:
                mod, fn = from_imports[name]
                return f"Dangerous call detected: {mod}.{fn} (via from-import '{name}')"

        # 2c. __import__('os').system()
        if (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Call)
                and isinstance(func.value.func, ast.Name)
                and func.value.func.id == "__import__"):
            if func.value.args and isinstance(func.value.args[0], ast.Constant):
                mod_name = func.value.args[0].value
                if isinstance(mod_name, str) and func.attr in DANGEROUS_MODULES.get(mod_name, set()):
                    return f"Dangerous call detected: __import__('{mod_name}').{func.attr}()"

        # 2d. getattr(obj, 'dangerous_name')()
        if (isinstance(func, ast.Call) and isinstance(func.func, ast.Name)
                and func.func.id == "getattr" and len(func.args) >= 2):
            obj_node = func.args[0]
            attr_node = func.args[1]
            if isinstance(attr_node, ast.Constant) and isinstance(attr_node.value, str):
                attr_name = attr_node.value
                if isinstance(obj_node, ast.Name):
                    mod = alias_map.get(obj_node.id)
                    if mod and attr_name in DANGEROUS_MODULES.get(mod, set()):
                        return f"Dangerous call detected: getattr({obj_node.id}, '{attr_name}')()"
                    if attr_name in DANGEROUS_BUILTINS:
                        return f"Dangerous builtin via getattr: getattr({obj_node.id}, '{attr_name}')()"

        # 2e. importlib.import_module('os')
        if (isinstance(func, ast.Attribute) and func.attr == "import_module"
                and isinstance(func.value, ast.Name)):
            obj = func.value.id
            mod = alias_map.get(obj)
            if mod and "import_module" in DANGEROUS_MODULES.get(mod, set()):
                if node.args and isinstance(node.args[0], ast.Constant):
                    imported = node.args[0].value
                    if isinstance(imported, str) and imported in DANGEROUS_MODULES:
                        return f"Dangerous dynamic import: {obj}.import_module('{imported}')"

        # 2f. globals()/vars()['__builtins__'][...]
        if isinstance(func, ast.Subscript):
            inner = func.value
            if (isinstance(inner, ast.Subscript) and isinstance(inner.slice, ast.Constant)
                    and inner.slice.value == "__builtins__"):
                if isinstance(func.slice, ast.Constant) and isinstance(func.slice.value, str):
                    if func.slice.value in DANGEROUS_BUILTIN_NAMES:
                        return f"Dangerous builtin access: [__builtins__]['{func.slice.value}']"
        if isinstance(func, ast.Attribute) and func.attr in DANGEROUS_BUILTIN_NAMES:
            if (isinstance(func.value, ast.Subscript)
                    and isinstance(func.value.slice, ast.Constant)
                    and func.value.slice.value == "__builtins__"):
                return f"Dangerous builtin access: [__builtins__].{func.attr}"

    # Step 3: flag bare __builtins__ access outside Call nodes
    for node in ast.walk(tree):
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Subscript)
                and isinstance(node.value.slice, ast.Constant)
                and node.value.slice.value == "__builtins__"
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str)
                and node.slice.value in DANGEROUS_BUILTIN_NAMES):
            return f"Dangerous builtin access: [__builtins__]['{node.slice.value}']"
        if (isinstance(node, ast.Attribute) and node.attr in DANGEROUS_BUILTIN_NAMES
                and isinstance(node.value, ast.Subscript)
                and isinstance(node.value.slice, ast.Constant)
                and node.value.slice.value == "__builtins__"):
            return f"Dangerous builtin access: [__builtins__].{node.attr}"

    return None


def _check_empty_functions(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_empty_function_body(node.body):
                return f"Empty function body detected: {node.name}"
    return None


def write_with_validation(
    filepath: str,
    content: str,
    workspace_root: str | None = None,
) -> dict[str, Any]:
    if workspace_root is not None:
        filepath = ensure_safe_path(filepath, workspace_root)

    original_content: str | None = None
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                original_content = f.read()
        except OSError as exc:
            return {"success": False, "message": f"Failed to read existing file for backup: {exc}",
                    "details": {"error": str(exc), "action": None}}

    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    except OSError as exc:
        return {"success": False, "message": f"Failed to create directory: {exc}",
                "details": {"error": str(exc), "action": None}}

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        return {"success": False, "message": f"Failed to write file: {exc}",
                "details": {"error": str(exc), "action": None}}

    if _is_python_file(filepath):
        try:
            py_compile.compile(filepath, doraise=True)
            tree = ast.parse(content)
            violation = _check_dangerous_calls(tree)
            if violation:
                raise ValueError(violation)
            violation = _check_empty_functions(tree)
            if violation:
                raise ValueError(violation)
        except (py_compile.PyCompileError, ValueError, SyntaxError) as exc:
            action = None
            if original_content is not None:
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(original_content)
                    action = "rolled_back"
                except OSError:
                    action = "rollback_failed"
            else:
                try:
                    os.remove(filepath)
                    action = "removed_new_file"
                except OSError:
                    action = "remove_failed"
            msg = f"Regression validation failed. Action: {action}. Detail: {exc}"
            _record_audit(filepath, False, msg)
            return {"success": False, "message": msg,
                    "details": {"error": str(exc), "action": action}}

    msg = "Write complete, passed validation."
    _record_audit(filepath, True, msg)
    return {"success": True, "message": msg}
