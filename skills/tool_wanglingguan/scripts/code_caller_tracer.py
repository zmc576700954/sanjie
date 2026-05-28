import os
import re
import argparse
from typing import List, Dict, Optional

# Try to import semantic_analyzer for AST fallback
try:
    from skills.tool_wanglingguan.scripts.semantic_analyzer import analyze_call_graph
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False


def _try_ast_first(project_root: str, target_class: str, target_method: str) -> Optional[List[Dict]]:
    """
    Attempt to use AST-based call graph analysis for Python files.
    Falls back to regex if AST fails or language is not supported.
    """
    if not AST_AVAILABLE:
        return None

    # Only use AST for Python files
    has_python = any(
        f.endswith('.py')
        for _, _, files in os.walk(project_root)
        for f in files
    )
    if not has_python:
        return None

    try:
        # Combine class and method if class is provided
        if target_class and target_class not in ('*', 'any'):
            target = f"{target_class}.{target_method}"
        else:
            target = target_method

        result = analyze_call_graph(project_root, target, include_indirect=False)
        ast_callers = result.get('call_sites', [])

        # Convert to the legacy format
        callers = []
        for site in ast_callers:
            callers.append({
                'file': site['file'],
                'line': site['line'],
                'context': site.get('context', f"{target_method}(...)"),
                'method_call': site.get('context', f"{target_method}(...)"),
            })
        return callers
    except Exception:
        return None


def find_callers(project_root: str, target_class: str, target_method: str, mode: str = 'auto') -> List[Dict]:
    """
    Find all call sites of a specific class::method within a project.

    Args:
        project_root: Project root directory to search.
        target_class: Class name to find call sites for.
        target_method: Method name to find call sites for.
        mode: 'auto' tries AST first then falls back to regex;
              'regex' uses only regex matching;
              'ast' uses only AST (returns empty if AST unavailable).

    Returns:
        List of dicts with file, line, and context.
    """
    # Try AST first if mode allows
    if mode in ('auto', 'ast'):
        ast_result = _try_ast_first(project_root, target_class, target_method)
        if ast_result is not None:
            return ast_result
        if mode == 'ast':
            return []

    # Regex fallback
    callers = []
    # Support Python (.), PHP (->, ::), and other languages
    # Negative lookbehind excludes 'function target(' declarations
    target_pattern = re.compile(
        rf'((?<!function\s)(?<!def\s)(?:\.|->|::)\s*{re.escape(target_method)}\s*\()',
        re.IGNORECASE
    )

    for root, dirs, files in os.walk(project_root):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {'vendor', 'node_modules', '.git', '__pycache__', '.pytest_cache'}]

        for filename in files:
            if not filename.endswith(('.php', '.py', '.js', '.ts', '.java', '.go')):
                continue

            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            except Exception:
                continue

            # Pre-compute class context for this file
            # For PHP: track which class $this refers to
            class_decls = {}  # line_number -> class_name
            for ci, cline in enumerate(lines):
                # PHP/Java/JS class declaration
                cls_match = re.search(r'\bclass\s+(\w+)', cline)
                if cls_match:
                    class_decls[ci + 1] = cls_match.group(1)
                # Python class declaration
                cls_match = re.search(r'^class\s+(\w+)', cline)
                if cls_match:
                    class_decls[ci + 1] = cls_match.group(1)

            for i, line in enumerate(lines, start=1):
                match = target_pattern.search(line)
                if match:
                    # Check if this line also references the target class
                    class_pattern = re.compile(rf'\b{re.escape(target_class)}\b', re.IGNORECASE)
                    explicit_class = class_pattern.search(line) or (i > 1 and class_pattern.search(lines[i - 2]))

                    # Also accept $this-> (PHP) and self./cls. (Python) as implicit class references
                    implicit_class = bool(re.search(r'\$this\s*->|self\s*\.|cls\s*\.', line))

                    # Or check if the current line is inside the target class scope
                    in_class_scope = False
                    if not explicit_class and not implicit_class:
                        for decl_line, decl_class in class_decls.items():
                            if decl_line <= i and decl_class.lower() == target_class.lower():
                                in_class_scope = True
                                break

                    if explicit_class or implicit_class or in_class_scope:
                        callers.append({
                            'file': filepath,
                            'line': i,
                            'context': line.strip(),
                            'method_call': match.group(1)
                        })

    return callers


def check_null_handling(project_root: str, file_path: str, line_number: int) -> Dict:
    """
    Check if a function/method at the given location has null/empty return handling.
    Looks for patterns like `if ($var === null)`, `if (empty($var))`, etc.
    """
    null_patterns = [
        r'if\s*\(\s*\$\w+\s*===?\s*(null|NULL)',
        r'if\s*\(\s*(empty|is_null|isset)\s*\(',
        r'\$\w+\s*\?->\s*\w+',   # PHP 8+ nullsafe operator (?-> only, not plain ->)
        r'\?\?\s*',  # null coalescing
        r'if\s*\(\s*\$\w+\s*\)',  # truthy check
        r'@\w+',  # error suppression (weak but present)
    ]

    result = {
        'has_null_check': False,
        'checks_found': [],
        'lines_checked': []
    }

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        result['error'] = str(e)
        return result

    # Check context around the target line (5 lines after for return handling)
    start = max(0, line_number - 1)
    end = min(len(lines), line_number + 8)

    for i in range(start, end):
        line = lines[i]
        result['lines_checked'].append(f"{i + 1}: {line.strip()}")
        for pattern in null_patterns:
            if re.search(pattern, line):
                result['has_null_check'] = True
                result['checks_found'].append({
                    'line': i + 1,
                    'pattern': pattern,
                    'code': line.strip()
                })

    return result


def main():
    parser = argparse.ArgumentParser(description="Code Caller Tracer - Find call sites and null handling")
    parser.add_argument("--project", required=True, help="Project root directory")
    parser.add_argument("--class", dest="target_class", help="Target class name")
    parser.add_argument("--method", dest="target_method", help="Target method name")
    parser.add_argument("--file", help="File path to check null handling")
    parser.add_argument("--line", type=int, help="Line number to check null handling")
    parser.add_argument("--mode", choices=['callers', 'null_check'], required=True,
                        help="Mode: 'callers' to find call sites, 'null_check' to check null handling")
    parser.add_argument("--trace-mode", choices=['auto', 'regex', 'ast'], default='auto',
                        help="Call tracing strategy: 'auto' tries AST first then regex, 'regex' uses only regex, 'ast' uses only AST")
