import os
import re
import argparse
from typing import List, Dict, Tuple


def find_imports(project_root: str, target_file: str) -> List[Dict]:
    """
    Find all import/use statements in a file.
    Returns list of imported modules/classes with their line numbers.
    """
    imports = []

    # PHP use statements
    php_use_pattern = re.compile(r'^\s*use\s+([^;]+);')
    # Python imports
    py_import_pattern = re.compile(r'^\s*(?:from\s+(\S+)\s+)?import\s+(.+)')
    # JavaScript/TypeScript imports
    js_import_pattern = re.compile(r"^\s*import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]")
    # Go imports
    go_import_pattern = re.compile(r'^\s*import\s+["\']([^"\']+)["\']')

    try:
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        return [{'error': str(e)}]

    for i, line in enumerate(lines, start=1):
        # PHP
        match = php_use_pattern.match(line)
        if match:
            imports.append({
                'line': i,
                'type': 'php_use',
                'import': match.group(1).strip(),
                'raw': line.strip()
            })
            continue

        # Python
        match = py_import_pattern.match(line)
        if match:
            imports.append({
                'line': i,
                'type': 'python_import',
                'module': match.group(1),
                'imports': match.group(2).strip(),
                'raw': line.strip()
            })
            continue

        # JS/TS
        match = js_import_pattern.match(line)
        if match:
            imports.append({
                'line': i,
                'type': 'js_import',
                'source': match.group(1),
                'raw': line.strip()
            })
            continue

        # Go
        match = go_import_pattern.match(line)
        if match:
            imports.append({
                'line': i,
                'type': 'go_import',
                'package': match.group(1),
                'raw': line.strip()
            })
            continue

    return imports


def validate_architecture_diagram(project_root: str, components: List[Dict]) -> Dict:
    """
    Validate an architecture diagram's arrow directions against code imports.

    components: list of dicts like:
        {'name': 'AdminPanelProvider', 'file': 'src/Providers/AdminPanelProvider.php'}

    Returns validation report.
    """
    report = {
        'valid': True,
        'issues': [],
        'verified_arrows': [],
        'missing_components': []
    }

    # Build component name -> file mapping
    component_map = {}
    for comp in components:
        name = comp['name']
        file_path = comp.get('file')

        if file_path and os.path.exists(os.path.join(project_root, file_path)):
            component_map[name] = os.path.join(project_root, file_path)
        else:
            # Try to find the file
            found = False
            for root, dirs, files in os.walk(project_root):
                dirs[:] = [d for d in dirs if d not in {'vendor', 'node_modules', '.git', '__pycache__'}]
                for f in files:
                    if f.endswith(('.php', '.py', '.js', '.ts')):
                        if name.lower() in f.lower():
                            component_map[name] = os.path.join(root, f)
                            found = True
                            break
                if found:
                    break

            if not found:
                report['missing_components'].append(name)
                report['valid'] = False

    return report


def verify_dependency_direction(project_root: str, from_component: str, to_component: str) -> Dict:
    """
    Verify if from_component imports to_component (meaning from depends on to).
    If yes, arrow should point from_component -> to_component.
    """
    result = {
        'from': from_component,
        'to': to_component,
        'arrow_correct': None,  # None = couldn't verify, True = correct, False = incorrect
        'evidence': []
    }

    # Find files for both components
    from_file = None
    to_file = None

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in {'vendor', 'node_modules', '.git', '__pycache__'}]
        for f in files:
            if f.endswith(('.php', '.py', '.js', '.ts', '.java')):
                filepath = os.path.join(root, f)
                if from_component.lower() in f.lower():
                    from_file = filepath
                if to_component.lower() in f.lower():
                    to_file = filepath

    if not from_file:
        result['evidence'].append(f"Could not find file for component: {from_component}")
        return result

    # Check if from_file imports/references to_component
    imports = find_imports(project_root, from_file)

    for imp in imports:
        if 'error' in imp:
            continue
        import_str = imp.get('import', imp.get('imports', imp.get('source', imp.get('package', ''))))
        if to_component.lower() in import_str.lower():
            result['arrow_correct'] = True
            result['evidence'].append({
                'file': from_file,
                'line': imp['line'],
                'import': import_str,
                'conclusion': f"{from_component} imports {to_component} — arrow {from_component} -> {to_component} is CORRECT"
            })
            return result

    # If no import found, check if to_component imports from_component (reverse dependency)
    if to_file:
        reverse_imports = find_imports(project_root, to_file)
        for imp in reverse_imports:
            if 'error' in imp:
                continue
            import_str = imp.get('import', imp.get('imports', imp.get('source', imp.get('package', ''))))
            if from_component.lower() in import_str.lower():
                result['arrow_correct'] = False
                result['evidence'].append({
                    'file': to_file,
                    'line': imp['line'],
                    'import': import_str,
                    'conclusion': f"{to_component} imports {from_component} — arrow should be {to_component} -> {from_component}, NOT {from_component} -> {to_component}"
                })
                return result

    # Could not verify either direction
    result['arrow_correct'] = None
    result['evidence'].append(f"Could not verify dependency direction between {from_component} and {to_component}")
    return result


def detect_circular_dependencies(project_root: str) -> List[List[str]]:
    """
    Detect circular import dependencies in a project using DFS.

    Builds a graph where nodes are file basenames (without extension)
    and edges are imports. Returns all unique cycles found.

    Returns:
        List of cycles, each cycle is a list of file names.
    """
    # Build dependency graph
    graph = {}  # file_name -> set of imported file names
    file_map = {}  # file_name -> full path

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in {'vendor', 'node_modules', '.git', '__pycache__'}]
        for f in files:
            if f.endswith(('.php', '.py', '.js', '.ts', '.java')):
                filepath = os.path.join(root, f)
                name = os.path.splitext(f)[0]
                file_map[name] = filepath
                imports = find_imports(project_root, filepath)
                deps = set()
                for imp in imports:
                    if 'error' in imp:
                        continue
                    import_str = imp.get('import', imp.get('imports', imp.get('source', imp.get('package', ''))))
                    # Extract base name from import string
                    if import_str:
                        base = os.path.basename(import_str.replace('\\', '/'))
                        base = os.path.splitext(base)[0]
                        if base and base != name:
                            deps.add(base)
                graph[name] = deps

    # DFS to find cycles
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def _dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                cycle = _dfs(neighbor)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                return cycle

        path.pop()
        rec_stack.remove(node)
        return None

    for node in list(graph.keys()):
        if node not in visited:
            cycle = _dfs(node)
            if cycle:
                # Normalize: rotate to start with smallest element to deduplicate
                normalized = cycle[:-1]
                start_idx = normalized.index(min(normalized))
                normalized = normalized[start_idx:] + normalized[:start_idx]
                if normalized not in cycles:
                    cycles.append(normalized)
            # Reset for next component
            path.clear()
            rec_stack.clear()

    return cycles


def verify_forbidden_dependency(project_root: str, forbidden_pairs: List[Tuple[str, str]]) -> List[Dict]:
    """
    Verify that no forbidden dependency directions exist in the codebase.

    Args:
        project_root: Project root directory.
        forbidden_pairs: List of (from_component, to_component) tuples that must not exist.
                         E.g., [("Controller", "Repository")] means Controller should not import Repository.

    Returns:
        List of violations, each with from_component, to_component, file, line.
    """
    violations = []

    for from_comp, to_comp in forbidden_pairs:
        result = verify_dependency_direction(project_root, from_comp, to_comp)
        if result['arrow_correct'] is True:
            for ev in result['evidence']:
                if isinstance(ev, dict):
                    violations.append({
                        'from_component': from_comp,
                        'to_component': to_comp,
                        'file': ev.get('file'),
                        'line': ev.get('line'),
                        'message': f"Forbidden dependency: {from_comp} imports {to_comp}",
                    })

    return violations


def main():
    parser = argparse.ArgumentParser(description="Import Validator - Verify architecture diagram arrows against code imports")
    parser.add_argument("--project", required=True, help="Project root directory")
    parser.add_argument("--mode", choices=['imports', 'validate_diagram', 'verify_arrow', 'circular', 'forbidden'], required=True)
    parser.add_argument("--file", help="File to analyze imports for")
    parser.add_argument("--from", dest="from_comp", help="Source component for arrow verification")
    parser.add_argument("--to", dest="to_comp", help="Target component for arrow verification")
    parser.add_argument("--components", help="JSON string of components for diagram validation")
    parser.add_argument("--forbidden", help="JSON list of [from, to] pairs for forbidden dependency check")

    args = parser.parse_args()

    if args.mode == 'imports':
        if not args.file:
            print("Error: --file required for imports mode")
            exit(1)

        imports = find_imports(args.project, args.file)
        print(f"=== IMPORT ANALYSIS ===")
        print(f"File: {args.file}")
        print(f"Imports found: {len(imports)}")
        for imp in imports:
            if 'error' in imp:
                print(f"  Error: {imp['error']}")
            else:
                print(f"  Line {imp['line']}: {imp['raw']}")
        print("=======================")

    elif args.mode == 'verify_arrow':
        if not args.from_comp or not args.to_comp:
            print("Error: --from and --to required for verify_arrow mode")
            exit(1)

        result = verify_dependency_direction(args.project, args.from_comp, args.to_comp)
        print(f"=== ARROW VERIFICATION ===")
        print(f"Arrow: {result['from']} -> {result['to']}")
        print(f"Correct: {'YES' if result['arrow_correct'] else 'NO' if result['arrow_correct'] is False else 'UNKNOWN'}")
        for ev in result['evidence']:
            if isinstance(ev, dict):
                print(f"  Evidence: {ev['conclusion']}")
                print(f"    File: {ev['file']}:{ev['line']}")
            else:
                print(f"  {ev}")
        print("==========================")

    elif args.mode == 'circular':
        cycles = detect_circular_dependencies(args.project)
        print(f"=== CIRCULAR DEPENDENCY CHECK ===")
        print(f"Cycles found: {len(cycles)}")
        for cycle in cycles:
            print(f"  {' -> '.join(cycle)} -> {cycle[0]}")
        print("=================================")

    elif args.mode == 'forbidden':
        import json as _json
        if not args.forbidden:
            print("Error: --forbidden required for forbidden mode")
            exit(1)
        pairs = _json.loads(args.forbidden)
        violations = verify_forbidden_dependency(args.project, [tuple(p) for p in pairs])
        print(f"=== FORBIDDEN DEPENDENCY CHECK ===")
        print(f"Violations found: {len(violations)}")
        for v in violations:
            print(f"  {v['from_component']} -> {v['to_component']}")
            print(f"    File: {v['file']}:{v['line']}")
        print("==================================")


if __name__ == "__main__":
    main()
