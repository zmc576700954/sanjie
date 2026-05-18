"""Analyze import dependencies between Python files."""
import ast
import os
from typing import Dict, List, Set


def analyze_dependencies(target_files: List[str], project_root: str = "") -> dict:
    """
    Parse import statements from target files and build a dependency graph.

    Returns:
        {
            "graph": {file: [files_it_imports]},
            "reverse_deps": {file: [files_that_import_it]},
            "topological_order": [file, ...],
            "circular_deps": [[file_a, file_b, ...]],
            "interface_boundaries": [file, ...],
        }
    """
    graph: Dict[str, List[str]] = {}
    reverse_deps: Dict[str, List[str]] = {f: [] for f in target_files}

    for filepath in target_files:
        imports = _extract_imports(filepath, project_root)
        # Filter to only imports that reference other target files
        relevant = [imp for imp in imports if imp in target_files]
        graph[filepath] = relevant
        for dep in relevant:
            if dep not in reverse_deps:
                reverse_deps[dep] = []
            reverse_deps[dep].append(filepath)

    topo_order = _topological_sort(graph, target_files)
    circular = _detect_cycles(graph)
    # Interface boundaries: files depended on by >= 3 others
    boundaries = [f for f, deps in reverse_deps.items() if len(deps) >= 3]

    return {
        "graph": graph,
        "reverse_deps": reverse_deps,
        "topological_order": topo_order,
        "circular_deps": circular,
        "interface_boundaries": boundaries,
    }


def _extract_imports(filepath: str, project_root: str) -> List[str]:
    """Extract import targets from a Python file using AST."""
    if not os.path.exists(filepath) or not filepath.endswith('.py'):
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                resolved = _resolve_module_to_file(alias.name, project_root)
                if resolved:
                    imports.append(resolved)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                resolved = _resolve_module_to_file(node.module, project_root)
                if resolved:
                    imports.append(resolved)

    return imports


def _resolve_module_to_file(module_name: str, project_root: str) -> str:
    """Attempt to resolve a dotted module name to a file path."""
    parts = module_name.replace('.', os.sep)
    candidates = [
        os.path.join(project_root, parts + '.py'),
        os.path.join(project_root, parts, '__init__.py'),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return os.path.normpath(candidate)
    return ""


def _topological_sort(graph: Dict[str, List[str]], all_files: List[str]) -> List[str]:
    """Return files in dependency order (leaves first)."""
    visited: Set[str] = set()
    result: List[str] = []
    temp_mark: Set[str] = set()

    def visit(node: str):
        if node in temp_mark:
            return  # Cycle detected, skip
        if node in visited:
            return
        temp_mark.add(node)
        for dep in graph.get(node, []):
            visit(dep)
        temp_mark.discard(node)
        visited.add(node)
        result.append(node)

    for f in all_files:
        visit(f)

    return result


def _detect_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Detect circular dependencies."""
    cycles: List[List[str]] = []
    visited: Set[str] = set()
    path: List[str] = []
    on_path: Set[str] = set()

    def dfs(node: str):
        if node in on_path:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        on_path.add(node)
        path.append(node)
        for dep in graph.get(node, []):
            dfs(dep)
        path.pop()
        on_path.discard(node)

    for node in graph:
        dfs(node)

    return cycles
