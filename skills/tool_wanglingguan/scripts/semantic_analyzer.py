"""Semantic Analyzer - AST-based code analysis.

Phase 1: Python-only (using standard library `ast` module).
Phase 4: Multi-language support via tree-sitter (PHP, JS/TS, Go).

Provides more precise analysis than regex-based tools:
- Call graph analysis with indirect call detection
- Data flow tracking from source to sink
- Cyclomatic complexity calculation
- Dependency extraction via AST
"""

import ast
import os
from typing import List, Dict, Optional, Set, Tuple, Any

# ───────────────────────────────────────────────
# Tree-sitter integration (Phase 4)
# ───────────────────────────────────────────────

TREE_SITTER_AVAILABLE = False
TS_LANGUAGES = {}

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_php
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_go

    TS_LANGUAGES = {
        '.py': Language(tree_sitter_python.language()),
        '.php': Language(tree_sitter_php.language_php()),
        '.js': Language(tree_sitter_javascript.language()),
        '.ts': Language(tree_sitter_typescript.language_typescript()),
        '.tsx': Language(tree_sitter_typescript.language_tsx()),
        '.go': Language(tree_sitter_go.language()),
    }
    TREE_SITTER_AVAILABLE = True
except ImportError:
    pass


# ───────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────


def analyze_call_graph(project_root: str, target_method: str, include_indirect: bool = False) -> Dict:
    """
    AST-level call graph analysis for Python, PHP, JS/TS, and Go code.

    Args:
        project_root: Project root directory to search.
        target_method: Method/function name to find call sites for.
                       Can be 'method_name' or 'ClassName.method_name'.
        include_indirect: If True, also finds calls through variables (e.g., obj.method()).

    Returns:
        Dict with 'call_sites' list, each containing file, line, context, call_type.
    """
    call_sites = []
    target_parts = target_method.split('.')
    target_name = target_parts[-1]
    target_class = target_parts[-2] if len(target_parts) > 1 else None

    # Python: use standard library ast module (faster, more precise)
    for filepath in _iter_python_files(project_root):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue

        visitor = _CallSiteVisitor(target_name, target_class, include_indirect)
        visitor.visit(tree)

        for site in visitor.sites:
            site['file'] = filepath
            call_sites.append(site)

    # Other languages: use tree-sitter
    if TREE_SITTER_AVAILABLE:
        ts_sites = _analyze_call_graph_treesitter(project_root, target_name)
        call_sites.extend(ts_sites)

    return {
        'target_method': target_method,
        'call_sites_found': len(call_sites),
        'call_sites': call_sites,
    }


def extract_dependencies(file_path: str) -> List[Dict]:
    """
    AST-level import extraction for Python, PHP, JS/TS, and Go files.

    Handles:
    - Python: import/from import with alias and star support
    - PHP: use declarations
    - JS/TS: import statements
    - Go: import specifications

    Returns:
        List of dicts with line, type, module, names, alias, is_star.
    """
    if not os.path.exists(file_path):
        return [{'error': f'File not found: {file_path}'}]

    # Non-Python: use tree-sitter
    if not file_path.endswith('.py') and TREE_SITTER_AVAILABLE:
        ts_imports = _extract_dependencies_treesitter(file_path)
        if ts_imports:
            return ts_imports

    # Python: use standard library ast module
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError) as e:
        return [{'error': str(e)}]

    visitor = _ImportVisitor()
    visitor.visit(tree)
    return visitor.imports


def detect_complexity(file_path: str) -> Dict:
    """
    Calculate cyclomatic complexity per function/method in a Python file.

    Cyclomatic complexity = 1 + number of decision points.
    Decision points: if, elif, for, while, except, with, assert,
    boolean 'and'/'or', ternary expressions, list/dict/set comprehensions.

    Returns:
        Dict with 'functions' list and 'max_complexity'.
    """
    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}', 'functions': [], 'max_complexity': 0}

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError) as e:
        return {'error': str(e), 'functions': [], 'max_complexity': 0}

    visitor = _ComplexityVisitor()
    visitor.visit(tree)

    max_complexity = max((f['complexity'] for f in visitor.functions), default=0)
    return {
        'file': file_path,
        'functions': visitor.functions,
        'max_complexity': max_complexity,
        'total_functions': len(visitor.functions),
    }


def trace_data_flow(project_root: str, source_pattern: str, sink_pattern: str) -> List[Dict]:
    """
    Trace sensitive data flow from source to sink in Python code.

    Args:
        project_root: Project root directory.
        source_pattern: Variable name or function call pattern that marks a data source
                        (e.g., 'request', 'input', 'file.read').
        sink_pattern: Function call pattern that marks a dangerous sink
                      (e.g., 'eval', 'exec', 'os.system', 'subprocess.call').

    Returns:
        List of data flow paths, each with source_line, sink_line, variable_chain.
    """
    flows = []
    source_names = _split_pattern(source_pattern)
    sink_names = _split_pattern(sink_pattern)

    for filepath in _iter_python_files(project_root):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue

        visitor = _DataFlowVisitor(source_names, sink_names)
        visitor.visit(tree)

        for flow in visitor.flows:
            flow['file'] = filepath
            flows.append(flow)

    return flows


def find_dead_code(project_root: str, entry_points: List[str]) -> List[Dict]:
    """
    Find functions/methods that are transitively unreachable from entry points.

    Builds a full project-wide call graph and performs BFS from entry points
    to identify all reachable functions. Anything not reached is flagged as
    potentially dead code.

    Args:
        project_root: Project root directory.
        entry_points: List of file paths that serve as entry points.

    Returns:
        List of potentially dead functions with file and line info.
    """
    from collections import deque

    all_functions = {}        # func_name -> list of {file, line, context}
    call_graph = {}           # caller_name -> set of callee_names

    # Phase 1: Build full call graph across all Python files
    for filepath in _iter_python_files(project_root):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue

        # Collect function definitions
        def_visitor = _FunctionDefVisitor()
        def_visitor.visit(tree)
        for func in def_visitor.functions:
            func['file'] = filepath
            func_key = func['name']
            all_functions.setdefault(func_key, []).append(func)

        # Build call graph edges for this file
        graph_visitor = _CallGraphVisitor()
        graph_visitor.visit(tree)
        for caller, callees in graph_visitor.edges.items():
            call_graph.setdefault(caller, set()).update(callees)

    # Phase 2: BFS from entry points to find all transitively reachable functions
    reachable = set()
    queue = deque()

    # Seed the queue with calls from entry point files
    for ep in entry_points:
        ep_path = os.path.join(project_root, ep) if not os.path.isabs(ep) else ep
        if not os.path.exists(ep_path):
            continue
        try:
            with open(ep_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue

        visitor = _CallCollector()
        visitor.visit(tree)
        for callee in visitor.calls:
            if callee not in reachable:
                reachable.add(callee)
                queue.append(callee)

    # BFS traversal through the call graph
    while queue:
        current = queue.popleft()
        for callee in call_graph.get(current, set()):
            if callee not in reachable:
                reachable.add(callee)
                queue.append(callee)

    # Phase 3: Flag functions not reachable from any entry point
    dead = []
    for func_name, locations in all_functions.items():
        # Skip dunder methods, main, test functions
        base_name = func_name.split('.')[-1] if '.' in func_name else func_name
        if base_name.startswith('__') or base_name in ('main', 'run'):
            continue
        if func_name not in reachable:
            # Also check base_name for non-class-qualified calls
            if base_name not in reachable:
                for loc in locations:
                    dead.append(loc)

    return dead


class _CallGraphVisitor(ast.NodeVisitor):
    """Builds caller -> callees edges for an entire file (all functions/methods)."""

    def __init__(self):
        self.edges: Dict[str, Set[str]] = {}
        self._current_func: Optional[str] = None
        self._current_class: Optional[str] = None

    def _qualified_name(self, name: str) -> str:
        if self._current_class:
            return f"{self._current_class}.{name}"
        return name

    def visit_ClassDef(self, node):
        prev = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev

    def visit_FunctionDef(self, node):
        prev_func = self._current_func
        self._current_func = self._qualified_name(node.name)
        self.generic_visit(node)
        self._current_func = prev_func

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Call(self, node):
        if self._current_func is not None:
            callee = None
            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr
            if callee:
                self.edges.setdefault(self._current_func, set()).add(callee)
        self.generic_visit(node)


# ───────────────────────────────────────────────
# Internal: AST Visitors
# ───────────────────────────────────────────────

class _CallSiteVisitor(ast.NodeVisitor):
    """Finds all call sites of a target method/function."""

    def __init__(self, target_name: str, target_class: Optional[str], include_indirect: bool):
        self.target_name = target_name
        self.target_class = target_class
        self.include_indirect = include_indirect
        self.sites: List[Dict] = []
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.source_lines: List[str] = []
        # Track variable -> class name mappings (e.g., svc = Service() => svc -> Service)
        self._var_to_class: Dict[str, str] = {}

    def visit(self, node):
        if hasattr(node, 'lineno'):
            # Store line numbers for context extraction
            pass
        super().visit(node)

    def visit_ClassDef(self, node):
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        prev_func = self.current_function
        self.current_function = node.name
        # Track assignments within this function
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Assign(self, node):
        """Track variable assignments like svc = Service() or svc = Service.create()."""
        if self.target_class:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    class_name = self._extract_class_from_call(node.value)
                    if class_name and class_name == self.target_class:
                        self._var_to_class[var_name] = class_name
        self.generic_visit(node)

    def _extract_class_from_call(self, node: ast.AST) -> Optional[str]:
        """Extract class name from constructor call or factory method.
        Handles: Service(), Service.create(), module.Service(), etc.
        """
        if isinstance(node, ast.Call):
            func = node.func
            # Direct: Service()
            if isinstance(func, ast.Name):
                return func.id
            # Factory: Service.create() or module.Service()
            if isinstance(func, ast.Attribute):
                # Service.create() -> return 'Service'
                if isinstance(func.value, ast.Name):
                    return func.value.id
        return None

    def visit_Call(self, node):
        call_info = self._analyze_call(node)
        if call_info:
            self.sites.append(call_info)
        self.generic_visit(node)

    def _analyze_call(self, node: ast.Call) -> Optional[Dict]:
        """Analyze a Call node to see if it matches the target."""
        line = getattr(node, 'lineno', 0)
        call_type = 'unknown'
        context = ''

        # Direct call: target_name()
        if isinstance(node.func, ast.Name) and node.func.id == self.target_name:
            call_type = 'direct'
            context = f"{self.target_name}(...)"
            return {
                'line': line,
                'context': context,
                'call_type': call_type,
                'in_class': self.current_class,
                'in_function': self.current_function,
            }

        # Method call: obj.target_name() or self.target_name()
        if isinstance(node.func, ast.Attribute) and node.func.attr == self.target_name:
            if isinstance(node.func.value, ast.Name):
                receiver = node.func.value.id
                call_type = f'method_call_via_{receiver}'
                context = f"{receiver}.{self.target_name}(...)"

                # If include_indirect is False, only match direct class references
                if not self.include_indirect and receiver not in ('self', 'cls', 'Self'):
                    # Check if the receiver is a known instance of the target class
                    is_known_instance = (
                        self.target_class and
                        self._var_to_class.get(receiver) == self.target_class
                    )
                    if self.target_class and receiver != self.target_class and not is_known_instance:
                        return None

                return {
                    'line': line,
                    'context': context,
                    'call_type': call_type,
                    'in_class': self.current_class,
                    'in_function': self.current_function,
                }

            # Chained call: obj.something.target_name()
            if self.include_indirect and isinstance(node.func.value, ast.Attribute):
                call_type = 'indirect_method_call'
                context = f"...{self.target_name}(...)"
                return {
                    'line': line,
                    'context': context,
                    'call_type': call_type,
                    'in_class': self.current_class,
                    'in_function': self.current_function,
                }

        return None


class _ImportVisitor(ast.NodeVisitor):
    """Extracts all import statements from a Python AST."""

    def __init__(self):
        self.imports: List[Dict] = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                'line': node.lineno,
                'type': 'import',
                'module': alias.name,
                'names': [alias.name],
                'alias': alias.asname,
                'is_star': False,
                'raw': ast.unparse(node) if hasattr(ast, 'unparse') else f"import {alias.name}",
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ''
        for alias in node.names:
            self.imports.append({
                'line': node.lineno,
                'type': 'from_import',
                'module': module,
                'names': [alias.name],
                'alias': alias.asname,
                'is_star': alias.name == '*',
                'raw': ast.unparse(node) if hasattr(ast, 'unparse') else f"from {module} import {alias.name}",
            })
        self.generic_visit(node)


class _ComplexityVisitor(ast.NodeVisitor):
    """Calculates cyclomatic complexity per function/method."""

    DECISION_NODE_TYPES = (
        ast.If, ast.While, ast.For, ast.ExceptHandler,
        ast.With, ast.Assert, ast.comprehension,
    )

    def __init__(self):
        self.functions: List[Dict] = []
        self._current_function: Optional[Dict] = None
        self._function_stack: List[Dict] = []

    def visit_FunctionDef(self, node):
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'complexity': 1,  # Base complexity
            'end_line': getattr(node, 'end_lineno', node.lineno),
        }
        self._function_stack.append(func_info)
        self.generic_visit(node)
        self._function_stack.pop()
        self.functions.append(func_info)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def _add_complexity(self, amount: int = 1):
        if self._function_stack:
            self._function_stack[-1]['complexity'] += amount

    def visit_If(self, node):
        self._add_complexity()
        # Also count elif blocks
        if hasattr(node, 'orelse') and node.orelse:
            for child in node.orelse:
                if isinstance(child, ast.If):
                    self._add_complexity()
        self.generic_visit(node)

    def visit_While(self, node):
        self._add_complexity()
        self.generic_visit(node)

    def visit_For(self, node):
        self._add_complexity()
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self._add_complexity()
        self.generic_visit(node)

    def visit_With(self, node):
        self._add_complexity()
        self.generic_visit(node)

    def visit_Assert(self, node):
        self._add_complexity()
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds a decision point
        self._add_complexity(len(node.values) - 1)
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self._add_complexity(len(node.generators))
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self._add_complexity(len(node.generators))
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self._add_complexity(len(node.generators))
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self._add_complexity(len(node.generators))
        self.generic_visit(node)

    def visit_IfExp(self, node):
        # Ternary: x if cond else y
        self._add_complexity()
        self.generic_visit(node)


class _DataFlowVisitor(ast.NodeVisitor):
    """Traces data flow from sources to sinks."""

    def __init__(self, source_names: List[str], sink_names: List[str]):
        self.source_names = set(source_names)
        self.sink_names = set(sink_names)
        self.flows: List[Dict] = []
        self.current_function: Optional[str] = None

    def visit_FunctionDef(self, node):
        prev = self.current_function
        self.current_function = node.name
        self._analyze_function(node)
        self.current_function = prev

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def _analyze_function(self, node):
        """Analyze a single function for data flows."""
        # Step 1: Find all source assignments
        # Step 2: Track variable propagation
        # Step 3: Find if tracked variables reach sinks

        # Collect all variable assignments and their sources
        assignments = {}  # var_name -> {line, source_type}

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        source_info = self._is_source_expr(child.value)
                        if source_info:
                            assignments[var_name] = {
                                'line': child.lineno,
                                'source_type': source_info,
                            }

            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name) and child.value:
                    var_name = child.target.id
                    source_info = self._is_source_expr(child.value)
                    if source_info:
                        assignments[var_name] = {
                            'line': child.lineno,
                            'source_type': source_info,
                        }

        if not assignments:
            return

        # Track propagation and find sinks
        tracked_vars = set(assignments.keys())
        propagated = set()

        for child in ast.walk(node):
            # Check for variable reassignments (propagation)
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if self._contains_tracked_var(child.value, tracked_vars):
                            tracked_vars.add(target.id)
                            propagated.add(target.id)

            # Check for sink calls with tracked variables
            if isinstance(child, ast.Call):
                sink_info = self._is_sink_call(child)
                if sink_info:
                    used_vars = self._extract_vars_from_node(child)
                    intersect = tracked_vars & used_vars
                    if intersect:
                        for var in intersect:
                            source = assignments.get(var, {'line': 0, 'source_type': 'unknown'})
                            self.flows.append({
                                'function': self.current_function,
                                'variable': var,
                                'source_line': source['line'],
                                'source_type': source['source_type'],
                                'sink_line': getattr(child, 'lineno', 0),
                                'sink_type': sink_info,
                                'is_propagated': var in propagated,
                            })

    def _is_source_expr(self, node: ast.AST) -> Optional[str]:
        """Check if an expression is a data source."""
        # Check for function calls like input(), request.get_json(), etc.
        if isinstance(node, ast.Call):
            func_name = self._get_call_name(node)
            if func_name:
                for src in self.source_names:
                    if src in func_name.lower():
                        return f'call:{func_name}'
        # Check for attribute access like request.form
        if isinstance(node, ast.Attribute):
            full = self._get_attribute_chain(node)
            for src in self.source_names:
                if src in full.lower():
                    return f'attr:{full}'
        # Check for subscript like request.form['name']
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute):
                full = self._get_attribute_chain(node.value)
                for src in self.source_names:
                    if src in full.lower():
                        return f'attr:{full}[...]'
        return None

    def _is_sink_call(self, node: ast.Call) -> Optional[str]:
        """Check if a call is a dangerous sink."""
        func_name = self._get_call_name(node)
        if func_name:
            for sink in self.sink_names:
                if sink in func_name.lower():
                    return f'call:{func_name}'
        return None

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the full name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_attribute_chain(node.func)
        return ''

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """Build 'module.submodule.function' from attribute chain."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))

    def _contains_tracked_var(self, node: ast.AST, tracked: Set[str]) -> bool:
        """Check if an expression contains any tracked variable."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in tracked:
                return True
        return False

    def _extract_vars_from_node(self, node: ast.AST) -> Set[str]:
        """Extract all variable names referenced in a node."""
        vars = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                vars.add(child.id)
        return vars


class _FunctionDefVisitor(ast.NodeVisitor):
    """Collects all function/method definitions."""

    def __init__(self):
        self.functions: List[Dict] = []
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node):
        prev = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev

    def visit_FunctionDef(self, node):
        name = node.name
        if self.current_class:
            name = f"{self.current_class}.{name}"
        self.functions.append({
            'name': name,
            'line': node.lineno,
            'context': f"def {node.name}(...)",
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)


class _CallCollector(ast.NodeVisitor):
    """Collects all function names called in a module."""

    def __init__(self):
        self.calls: Set[str] = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        self.generic_visit(node)


# ───────────────────────────────────────────────
# Tree-sitter Multi-Language Analysis (Phase 4)
# ───────────────────────────────────────────────

_SOURCE_EXTENSIONS = {'.py', '.php', '.js', '.ts', '.tsx', '.go'}


def _get_language_for_file(filepath: str) -> Optional[Any]:
    """Get the tree-sitter Language for a file based on extension."""
    if not TREE_SITTER_AVAILABLE:
        return None
    ext = os.path.splitext(filepath)[1].lower()
    return TS_LANGUAGES.get(ext)


def _parse_with_treesitter(filepath: str, language: Any) -> Optional[Any]:
    """Parse a file with tree-sitter and return the root node."""
    try:
        with open(filepath, 'rb') as f:
            source_bytes = f.read()
        parser = Parser(language)
        tree = parser.parse(source_bytes)
        return tree.root_node
    except Exception:
        return None


def _ts_find_call_sites(root_node: Any, target_name: str, filepath: str) -> List[Dict]:
    """Find call sites in a tree-sitter AST."""
    sites = []

    def _walk(node, depth=0):
        # PHP: function_call_expression, member_call_expression
        # JS/TS: call_expression
        # Go: call_expression
        if node.type in ('function_call_expression', 'member_call_expression', 'call_expression'):
            func_name = _ts_get_call_name(node)
            if func_name and target_name in func_name:
                line = node.start_point[0] + 1
                context = _ts_get_line_text(filepath, line)
                sites.append({
                    'line': line,
                    'context': context.strip() if context else f"{func_name}(...)",
                    'call_type': 'direct' if func_name == target_name else 'method_call',
                    'in_function': None,
                    'in_class': None,
                })

        for child in node.children:
            _walk(child, depth + 1)

    _walk(root_node)
    return sites


def _ts_get_call_name(node: Any) -> str:
    """Extract function/method name from a call_expression node."""
    # Handle PHP member_call_expression directly: $obj->method()
    if node.type == 'member_call_expression':
        for child in node.children:
            if child.type == 'name':
                return child.text.decode('utf-8', errors='ignore')
        return ''

    # The function being called is typically the first child
    func_node = None
    for child in node.children:
        if child.type not in ('(', ')', 'argument_list', 'type_arguments'):
            func_node = child
            break

    if not func_node:
        return ''

    # Direct call: identifier
    if func_node.type == 'identifier':
        return func_node.text.decode('utf-8', errors='ignore')

    # Method call: member_expression (obj->method) or field_expression (obj.method)
    if func_node.type in ('member_expression', 'field_expression', 'selector_expression'):
        # Find the property/field name (last part)
        for child in reversed(func_node.children):
            if child.type in ('name', 'identifier', 'property_identifier', 'field_identifier'):
                return child.text.decode('utf-8', errors='ignore')
        return func_node.text.decode('utf-8', errors='ignore')

    # Namespaced call: name (PHP \Namespace\Class::method)
    if func_node.type == 'name':
        text = func_node.text.decode('utf-8', errors='ignore')
        # Return just the method name (last :: or \ part)
        if '::' in text:
            return text.split('::')[-1]
        if '\\' in text:
            return text.split('\\')[-1]
        return text

    return ''


def _ts_get_line_text(filepath: str, line_number: int) -> str:
    """Get the text of a specific line from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if 1 <= line_number <= len(lines):
                return lines[line_number - 1]
    except Exception:
        pass
    return ''


def _ts_extract_imports(root_node: Any, filepath: str) -> List[Dict]:
    """Extract import statements from a tree-sitter AST."""
    imports = []

    def _walk(node):
        # PHP: namespace_use_declaration
        if node.type == 'namespace_use_declaration':
            text = node.text.decode('utf-8', errors='ignore').strip()
            line = node.start_point[0] + 1
            imports.append({
                'line': line,
                'type': 'php_use',
                'import': text,
                'raw': text,
            })

        # PHP: use_declaration (inside trait_use_statement etc.)
        elif node.type == 'use_declaration':
            text = node.text.decode('utf-8', errors='ignore').strip()
            line = node.start_point[0] + 1
            imports.append({
                'line': line,
                'type': 'php_use',
                'import': text,
                'raw': text,
            })

        # JS/TS: import_statement
        elif node.type == 'import_statement':
            text = node.text.decode('utf-8', errors='ignore').strip()
            line = node.start_point[0] + 1
            imports.append({
                'line': line,
                'type': 'js_import',
                'source': _ts_get_import_source(node),
                'raw': text,
            })

        # Go: import_spec (inside import_declaration)
        elif node.type == 'import_spec':
            text = node.text.decode('utf-8', errors='ignore').strip()
            line = node.start_point[0] + 1
            imports.append({
                'line': line,
                'type': 'go_import',
                'package': _ts_get_go_import_path(node),
                'raw': text,
            })

        for child in node.children:
            _walk(child)

    _walk(root_node)
    return imports


def _ts_get_import_source(node: Any) -> str:
    """Extract import source path from JS/TS import statement."""
    for child in node.children:
        if child.type == 'string':
            text = child.text.decode('utf-8', errors='ignore')
            return text.strip('"\'')
        elif child.type == 'string_fragment':
            return child.text.decode('utf-8', errors='ignore')
    return ''


def _ts_get_go_import_path(node: Any) -> str:
    """Extract package path from Go import_spec."""
    for child in node.children:
        if child.type == 'interpreted_string_literal':
            text = child.text.decode('utf-8', errors='ignore')
            return text.strip('"')
        elif child.type == 'raw_string_literal':
            text = child.text.decode('utf-8', errors='ignore')
            return text.strip('`')
    return ''


def _analyze_call_graph_treesitter(project_root: str, target_method: str) -> List[Dict]:
    """Use tree-sitter to analyze call graph for non-Python languages."""
    call_sites = []
    for filepath in _iter_source_files(project_root):
        lang = _get_language_for_file(filepath)
        if not lang or filepath.endswith('.py'):
            continue

        root = _parse_with_treesitter(filepath, lang)
        if not root:
            continue

        sites = _ts_find_call_sites(root, target_method, filepath)
        for site in sites:
            site['file'] = filepath
            call_sites.append(site)

    return call_sites


def _extract_dependencies_treesitter(file_path: str) -> List[Dict]:
    """Use tree-sitter to extract dependencies for non-Python files."""
    lang = _get_language_for_file(file_path)
    if not lang or file_path.endswith('.py'):
        return []

    root = _parse_with_treesitter(file_path, lang)
    if not root:
        return [{'error': f'Failed to parse file with tree-sitter: {file_path}'}]

    return _ts_extract_imports(root, file_path)


# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────


def _iter_source_files(project_root: str):
    """Yield all source files under project_root, skipping common non-source dirs."""
    skip_dirs = {'venv', '.venv', 'env', '.env', 'node_modules', '.git', '__pycache__',
                 '.pytest_cache', 'build', 'dist', '.eggs', '*.egg-info'}
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.endswith('.egg-info')]
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in _SOURCE_EXTENSIONS:
                yield os.path.join(root, filename)


def _iter_python_files(project_root: str):
    """Yield all .py files under project_root, skipping common non-source dirs."""
    skip_dirs = {'venv', '.venv', 'env', '.env', 'node_modules', '.git', '__pycache__',
                 '.pytest_cache', 'build', 'dist', '.eggs', '*.egg-info'}
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.endswith('.egg-info')]
        for filename in files:
            if filename.endswith('.py'):
                yield os.path.join(root, filename)


def _split_pattern(pattern: str) -> List[str]:
    """Split a comma-separated pattern string into parts."""
    return [p.strip() for p in pattern.split(',') if p.strip()]


# ───────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Semantic Analyzer - AST-based code analysis')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # analyze_call_graph
    p = subparsers.add_parser('call_graph', help='Analyze call graph')
    p.add_argument('--project', required=True)
    p.add_argument('--method', required=True)
    p.add_argument('--indirect', action='store_true')

    # extract_dependencies
    p = subparsers.add_parser('dependencies', help='Extract import dependencies')
    p.add_argument('--file', required=True)

    # detect_complexity
    p = subparsers.add_parser('complexity', help='Detect cyclomatic complexity')
    p.add_argument('--file', required=True)

    # trace_data_flow
    p = subparsers.add_parser('data_flow', help='Trace data flow from source to sink')
    p.add_argument('--project', required=True)
    p.add_argument('--source', required=True)
    p.add_argument('--sink', required=True)

    # find_dead_code
    p = subparsers.add_parser('dead_code', help='Find potentially dead code')
    p.add_argument('--project', required=True)
    p.add_argument('--entry-points', required=True, nargs='+')

    args = parser.parse_args()

    if args.command == 'call_graph':
        result = analyze_call_graph(args.project, args.method, args.indirect)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'dependencies':
        result = extract_dependencies(args.file)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'complexity':
        result = detect_complexity(args.file)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'data_flow':
        result = trace_data_flow(args.project, args.source, args.sink)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'dead_code':
        result = find_dead_code(args.project, args.entry_points)
        print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
