import os
import re
import argparse
from typing import List, Dict, Optional


def find_callers(project_root: str, target_class: str, target_method: str) -> List[Dict]:
    """
    Find all call sites of a specific class::method within a project.
    Returns list of dicts with file, line, and context.
    """
    callers = []
    target_pattern = re.compile(
        rf'((?:->|::)\s*{re.escape(target_method)}\s*\(.*?\))',
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

            for i, line in enumerate(lines, start=1):
                match = target_pattern.search(line)
                if match:
                    # Check if this line also references the target class
                    class_pattern = re.compile(rf'\b{re.escape(target_class)}\b', re.IGNORECASE)
                    if class_pattern.search(line) or (i > 1 and class_pattern.search(lines[i - 2])):
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
        r'\$\w+\s*\??\.\s*\w+',  # PHP 8+ nullsafe operator
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

    args = parser.parse_args()

    if args.mode == 'callers':
        if not args.target_class or not args.target_method:
            print("Error: --class and --method required for callers mode")
            exit(1)

        callers = find_callers(args.project, args.target_class, args.target_method)
        print(f"=== CALLER TRACE REPORT ===")
        print(f"Target: {args.target_class}::{args.target_method}")
        print(f"Call sites found: {len(callers)}")
        for c in callers:
            print(f"\nFile: {c['file']}:{c['line']}")
            print(f"  Context: {c['context']}")
        print("===========================")

    elif args.mode == 'null_check':
        if not args.file or not args.line:
            print("Error: --file and --line required for null_check mode")
            exit(1)

        result = check_null_handling(args.project, args.file, args.line)
        print(f"=== NULL HANDLING CHECK ===")
        print(f"File: {args.file}:{args.line}")
        print(f"Has null check: {'YES' if result['has_null_check'] else 'NO'}")
        if result['checks_found']:
            print("Checks found:")
            for check in result['checks_found']:
                print(f"  Line {check['line']}: {check['code']}")
        print("===========================")


if __name__ == "__main__":
    main()
