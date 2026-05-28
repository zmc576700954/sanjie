"""
Security configuration for Skill Taie's AST regression validation.

All dangerous-module lists, dangerous builtins, and detection policies
are defined here so they can be extended without modifying core logic.
"""

DANGEROUS_MODULES: dict[str, set[str]] = {
    "os": {"system", "popen", "startfile"},
    "subprocess": {
        "run", "Popen", "call", "check_output", "check_call",
        "getoutput", "getstatusoutput",
    },
    "importlib": {"import_module"},
    "shutil": {"rmtree", "move", "copy", "copy2", "copytree"},
}

DANGEROUS_BUILTINS: set[str] = {"eval", "exec", "compile"}

DANGEROUS_BUILTIN_NAMES: set[str] = {"eval", "exec", "compile", "breakpoint"}

TREAT_ELLIPSIS_AS_EMPTY: bool = True

PYTHON_EXTENSIONS: set[str] = {".py", ".pyi", ".pyw"}
