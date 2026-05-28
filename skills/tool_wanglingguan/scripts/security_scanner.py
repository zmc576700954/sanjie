"""Security Scanner - Lightweight security pattern scanning.

A regex + AST hybrid approach for detecting security issues.
Inspired by Semgrep's rule design but intentionally lightweight.

Capabilities:
- scan_secrets: Hardcoded keys/tokens (entropy + pattern dual detection)
- scan_sql_injection: SQL injection patterns with variable propagation
- scan_xss_vectors: XSS vectors in templates/strings
- scan_misconfiguration: Dangerous config values
- scan_dangerous_operations: Dangerous instructions in Agent outputs
"""

import ast
import math
import os
import re
from typing import List, Dict, Optional, Set, Tuple


# ───────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────


def _read_file_lines(file_path: str) -> Optional[tuple[str, list[str]]]:
    """Read a file and return (content, lines). Returns None on error."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content, content.split('\n')
    except Exception:
        return None


def scan_secrets(file_path: str) -> List[Dict]:
    """
    Detect hardcoded secrets, API keys, tokens, and passwords.

    Uses dual detection:
    1. Pattern matching: regex for common secret formats
    2. Entropy analysis: high-entropy strings that look like secrets

    Returns:
        List of findings with line, type, severity, evidence.
    """
    result = _read_file_lines(file_path)
    if result is None:
        return [{'error': f'File not found: {file_path}'}]
    content, lines = result

    findings = []
    seen_lines = set()

    for i, line in enumerate(lines, start=1):
        # Pattern-based detection
        for pattern_name, pattern in _SECRET_PATTERNS.items():
            for match in pattern.finditer(line):
                secret_value = match.group('secret')
                if secret_value and len(secret_value) >= 8:
                    entropy = _calculate_entropy(secret_value)
                    # Per-pattern entropy thresholds: patterns with fixed prefixes
                    # (e.g., AWS keys start with 'AKIA') have inherently lower entropy,
                    # so the regex match itself is already a strong detection signal.
                    _ENTROPY_THRESHOLDS = {
                        'password': 3.0,
                        'jwt_secret': 3.0,
                        'aws_key': 3.0,     # AKIA prefix reduces entropy
                        'aws_secret': 3.0,   # AWS secrets have structured format
                        'bearer_token': 3.0,  # JWT prefix 'eyJ' reduces entropy
                    }
                    threshold = _ENTROPY_THRESHOLDS.get(pattern_name, 3.8)
                    if entropy >= threshold:
                        findings.append({
                            'line': i,
                            'type': 'hardcoded_secret',
                            'subtype': pattern_name,
                            'severity': 'critical',
                            'evidence': line.strip(),
                            'entropy': round(entropy, 2),
                            'message': f"Potential hardcoded {pattern_name} detected (entropy={entropy:.2f})",
                        })
                        seen_lines.add(i)

        # Entropy-based detection for high-entropy strings that look like secrets
        # but didn't match known patterns
        for match in _HIGH_ENTROPY_STRING.finditer(line):
            value = match.group(1)
            # Skip if already caught by pattern detection
            if i in seen_lines:
                continue
            if len(value) >= 20:
                entropy = _calculate_entropy(value)
                if entropy >= 5.0:
                    findings.append({
                        'line': i,
                        'type': 'high_entropy_string',
                        'subtype': 'unknown_secret',
                        'severity': 'high',
                        'evidence': line.strip(),
                        'entropy': round(entropy, 2),
                        'message': f"High-entropy string detected (entropy={entropy:.2f}), possible secret",
                    })
                    seen_lines.add(i)

    # Also scan for assignment patterns that look like secrets
    try:
        tree = ast.parse(content)
        _check_secret_assignments(tree, findings)
    except SyntaxError:
        pass

    return findings


def scan_sql_injection(file_path: str) -> List[Dict]:
    """
    Detect SQL injection vulnerabilities.

    Patterns checked:
    - String concatenation in SQL queries
    - f-string formatting in SQL
    - String .format() with variables in SQL
    - execute() calls with non-parameterized queries

    Returns:
        List of findings with line, severity, evidence, fix suggestion.
    """
    result = _read_file_lines(file_path)
    if result is None:
        return [{'error': f'File not found: {file_path}'}]
    content, lines = result

    findings = []
    seen_lines = set()

    # Regex-based detection for non-Python files or fallback
    for i, line in enumerate(lines, start=1):
        # Check for string concatenation in SQL-related strings
        if _SQL_CONCAT_PATTERN.search(line):
            findings.append({
                'line': i,
                'type': 'sql_injection',
                'subtype': 'string_concatenation',
                'severity': 'critical',
                'evidence': line.strip(),
                'message': 'Potential SQL injection via string concatenation',
                'fix': 'Use parameterized queries (prepared statements) instead',
            })
            seen_lines.add(i)

        # Check for f-strings in SQL
        if _SQL_FSTRING_PATTERN.search(line):
            findings.append({
                'line': i,
                'type': 'sql_injection',
                'subtype': 'f_string_in_sql',
                'severity': 'critical',
                'evidence': line.strip(),
                'message': 'Potential SQL injection via f-string interpolation',
                'fix': 'Use parameterized queries instead of f-string formatting',
            })
            seen_lines.add(i)

        # Check for .format() in SQL
        if _SQL_FORMAT_PATTERN.search(line):
            findings.append({
                'line': i,
                'type': 'sql_injection',
                'subtype': 'format_method',
                'severity': 'critical',
                'evidence': line.strip(),
                'message': 'Potential SQL injection via .format() in SQL',
                'fix': 'Use parameterized queries instead',
            })
            seen_lines.add(i)

    # AST-based detection for Python files
    try:
        tree = ast.parse(content)
        visitor = _SQLInjectionVisitor()
        visitor.visit(tree)
        for finding in visitor.findings:
            # Merge with regex findings to avoid duplicates
            if finding['line'] not in seen_lines:
                findings.append(finding)
    except SyntaxError:
        pass

    return findings


def scan_xss_vectors(file_path: str) -> List[Dict]:
    """
    Detect XSS (Cross-Site Scripting) vectors.

    Checks for:
    - Unescaped user input in HTML output
    - render_template with unsafe variables
    - innerHTML assignments
    - document.write with variables

    Returns:
        List of findings.
    """
    result = _read_file_lines(file_path)
    if result is None:
        return [{'error': f'File not found: {file_path}'}]
    _, lines = result

    findings = []

    for i, line in enumerate(lines, start=1):
        # innerHTML with variable
        if _INNERHTML_PATTERN.search(line):
            findings.append({
                'line': i,
                'type': 'xss',
                'subtype': 'innerHTML_assignment',
                'severity': 'high',
                'evidence': line.strip(),
                'message': 'Potential XSS via innerHTML assignment with variable',
                'fix': 'Use textContent instead, or sanitize input with DOMPurify',
            })

        # document.write
        if _DOC_WRITE_PATTERN.search(line):
            findings.append({
                'line': i,
                'type': 'xss',
                'subtype': 'document_write',
                'severity': 'high',
                'evidence': line.strip(),
                'message': 'Potential XSS via document.write with variable',
                'fix': 'Avoid document.write; use safe DOM manipulation instead',
            })

        # render_template_string with user input
        if _RENDER_STRING_PATTERN.search(line):
            findings.append({
                'line': i,
                'type': 'xss',
                'subtype': 'render_template_string',
                'severity': 'high',
                'evidence': line.strip(),
                'message': 'Potential XSS via render_template_string with user input',
                'fix': 'Use render_template with proper escaping, or Jinja autoescape',
            })

        # mark_safe in Django/Jinja
        if _MARK_SAFE_PATTERN.search(line):
            findings.append({
                'line': i,
                'type': 'xss',
                'subtype': 'mark_safe',
                'severity': 'high',
                'evidence': line.strip(),
                'message': 'mark_safe() disables HTML escaping - potential XSS',
                'fix': 'Only use mark_safe() with trusted, sanitized content',
            })

    return findings


def scan_misconfiguration(file_path: str) -> List[Dict]:
    """
    Detect dangerous configuration values.

    Checks:
    - debug=true / DEBUG = True
    - Weak password policies
    - Exposed admin endpoints
    - CORS wildcards
    - JWT without expiration
    - SQLAlchemy echo=True in production

    Returns:
        List of findings.
    """
    result = _read_file_lines(file_path)
    if result is None:
        return [{'error': f'File not found: {file_path}'}]
    _, lines = result

    findings = []

    for i, line in enumerate(lines, start=1):
        for check_name, pattern_info in _MISCONFIG_PATTERNS.items():
            pattern = pattern_info['pattern']
            severity = pattern_info.get('severity', 'warning')
            message = pattern_info.get('message', f'Dangerous configuration: {check_name}')
            fix = pattern_info.get('fix', 'Review and fix this configuration')

            if pattern.search(line):
                findings.append({
                    'line': i,
                    'type': 'misconfiguration',
                    'subtype': check_name,
                    'severity': severity,
                    'evidence': line.strip(),
                    'message': message,
                    'fix': fix,
                })

    return findings


def scan_dangerous_operations(content: str) -> List[Dict]:
    """
    Scan Agent output content for dangerous operation instructions.

    This is specifically for reviewing LLM/Agent outputs to prevent
    excessive agency (OWASP LLM Top 10 2025 - LLM06).

    Detects:
    - File deletion commands (rm -rf, del /f /s /q)
    - Permission changes (chmod 777, icacls with full)
    - Database destructive operations (DROP TABLE, TRUNCATE)
    - System-level commands that modify OS state
    - Code that uses eval()/exec() on untrusted input

    Returns:
        List of findings with severity, evidence, and recommendation.
    """
    findings = []
    lines = content.split('\n')

    for i, line in enumerate(lines, start=1):
        for check_name, pattern_info in _DANGEROUS_OP_PATTERNS.items():
            pattern = pattern_info['pattern']
            severity = pattern_info.get('severity', 'critical')
            message = pattern_info.get('message', f'Dangerous operation detected: {check_name}')
            recommendation = pattern_info.get('recommendation', 'Review this operation carefully')

            if pattern.search(line):
                findings.append({
                    'line': i,
                    'type': 'dangerous_operation',
                    'subtype': check_name,
                    'severity': severity,
                    'evidence': line.strip(),
                    'message': message,
                    'recommendation': recommendation,
                })

    return findings


# ───────────────────────────────────────────────
# Pattern Definitions
# ───────────────────────────────────────────────

# Secret detection patterns
_SECRET_PATTERNS = {
    'api_key': re.compile(
        r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[\'"](?P<secret>[a-zA-Z0-9_\-]{16,})[\'"]'
    ),
    'aws_key': re.compile(
        r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[:=]\s*[\'"](?P<secret>AKIA[0-9A-Z]{16})[\'"]'
    ),
    'aws_secret': re.compile(
        r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*[\'"](?P<secret>[0-9a-zA-Z/+=]{40})[\'"]'
    ),
    'github_token': re.compile(
        r'(?i)(github[_-]?token|gh[_-]?token)\s*[:=]\s*[\'"](?P<secret>ghp_[a-zA-Z0-9]{36,})[\'"]'
    ),
    'jwt_secret': re.compile(
        r'(?i)(jwt[_-]?secret|secret[_-]?key)\s*[:=]\s*[\'"](?P<secret>[a-zA-Z0-9_\-]{16,})[\'"]'
    ),
    'private_key': re.compile(
        r'(?i)(private[_-]?key|rsa[_-]?private)\s*[:=]\s*[\'"](?P<secret>.{50,})[\'"]'
    ),
    'password': re.compile(
        r'(?i)(password|passwd|pwd)\s*[:=]\s*[\'"](?P<secret>.{8,})[\'"]'
    ),
    'bearer_token': re.compile(
        r'(?i)(bearer\s+[\'"]?(?P<secret>eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)[\'"]?)'
    ),
}

_HIGH_ENTROPY_STRING = re.compile(r'[\'"]([A-Za-z0-9+/=_-]{20,})[\'"]')

# SQL injection patterns
_SQL_CONCAT_PATTERN = re.compile(
    r'(?i)(execute|query|cursor\.execute)\s*\(\s*[\'"].*?(\+|\%\s*\(|\.format\(|f[\'"]).*?[\'"]'
)
_SQL_FSTRING_PATTERN = re.compile(
    r'(?i)(execute|query|cursor\.execute)\s*\(\s*f[\'"].*?\{.*?\}.*?[\'"]'
)
_SQL_FORMAT_PATTERN = re.compile(
    r'(?i)(execute|query|cursor\.execute)\s*\(\s*[\'"].*?\{.*?\}.*?[\'"]\s*\.\s*format\s*\('
)

# XSS patterns
_INNERHTML_PATTERN = re.compile(r'(?i)\.innerHTML\s*=\s*[^\'"]')
_DOC_WRITE_PATTERN = re.compile(r'(?i)document\.write\s*\(')
_RENDER_STRING_PATTERN = re.compile(r'(?i)render_template_string\s*\(')
_MARK_SAFE_PATTERN = re.compile(r'(?i)mark_safe\s*\(')

# Misconfiguration patterns
_MISCONFIG_PATTERNS = {
    'debug_enabled': {
        'pattern': re.compile(r'(?i)^\s*(debug|DEBUG)\s*=\s*True'),
        'severity': 'critical',
        'message': 'Debug mode enabled - exposes sensitive information in production',
        'fix': 'Set DEBUG = False in production configurations',
    },
    'weak_password_hash': {
        'pattern': re.compile(r'(?i)(md5|sha1)\s*\('),
        'severity': 'high',
        'message': 'Weak password hashing algorithm detected (MD5/SHA1)',
        'fix': 'Use bcrypt, scrypt, or Argon2 for password hashing',
    },
    'cors_wildcard': {
        'pattern': re.compile(r'(?i)(cors|cors_allowed_origins).*?[\'"]\*[\'"]'),
        'severity': 'high',
        'message': 'CORS wildcard (*) allows requests from any origin',
        'fix': 'Specify explicit allowed origins instead of wildcard',
    },
    'jwt_no_expiry': {
        'pattern': re.compile(r'(?i)(jwt|token).*?expire.*?(None|null|false|0\b)', re.IGNORECASE),
        'severity': 'high',
        'message': 'JWT token has no expiration - security risk',
        'fix': 'Set a reasonable expiration time for JWT tokens',
    },
    'sqlalchemy_echo': {
        'pattern': re.compile(r'(?i)echo\s*=\s*True'),
        'severity': 'warning',
        'message': 'SQLAlchemy echo=True logs all SQL queries - may leak sensitive data',
        'fix': 'Set echo=False in production, or use a dedicated audit log',
    },
    'eval_enabled': {
        'pattern': re.compile(r'(?i)\beval\s*\('),
        'severity': 'critical',
        'message': 'eval() executes arbitrary code - severe security risk',
        'fix': 'Use ast.literal_eval() for safe parsing, or redesign to avoid dynamic execution',
    },
    'pickle_load': {
        'pattern': re.compile(r'(?i)pickle\.loads?\s*\('),
        'severity': 'high',
        'message': 'pickle.load() can execute arbitrary code on deserialization',
        'fix': 'Use json, msgpack, or other safe serialization formats',
    },
    'ssl_verify_disabled': {
        'pattern': re.compile(r'(?i)(verify\s*=\s*False|cert_reqs\s*=\s*CERT_NONE)'),
        'severity': 'high',
        'message': 'SSL certificate verification disabled - vulnerable to MITM attacks',
        'fix': 'Always verify SSL certificates in production',
    },
}

# Dangerous operation patterns (for Agent output review)
_DANGEROUS_OP_PATTERNS = {
    'rm_rf': {
        'pattern': re.compile(r'\brm\s+-rf\b|\brm\s+-r\s+-f\b'),
        'severity': 'critical',
        'message': 'Destructive file deletion command detected (rm -rf)',
        'recommendation': 'Use shutil.rmtree() with explicit path validation, or require explicit confirmation',
    },
    'chmod_777': {
        'pattern': re.compile(r'\bchmod\s+777\b|\bchmod\s+a+rwx\b'),
        'severity': 'critical',
        'message': 'Overly permissive file permissions (chmod 777)',
        'recommendation': 'Use principle of least privilege - 644 for files, 755 for directories',
    },
    'drop_table': {
        'pattern': re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        'severity': 'critical',
        'message': 'Destructive database operation detected (DROP TABLE)',
        'recommendation': 'Require multi-step confirmation before executing DROP operations',
    },
    'truncate_table': {
        'pattern': re.compile(r'\bTRUNCATE\s+TABLE\b', re.IGNORECASE),
        'severity': 'high',
        'message': 'Data-destructive operation detected (TRUNCATE TABLE)',
        'recommendation': 'Use DELETE with WHERE clause for selective removal, or require confirmation',
    },
    'eval_untrusted': {
        'pattern': re.compile(r'\beval\s*\(.*?(input|request|user)'),
        'severity': 'critical',
        'message': 'eval() with potentially untrusted input detected',
        'recommendation': 'Never use eval() on user input. Use json.loads(), ast.literal_eval(), or redesign',
    },
    'exec_untrusted': {
        'pattern': re.compile(r'\bexec\s*\(.*?(input|request|user)'),
        'severity': 'critical',
        'message': 'exec() with potentially untrusted input detected',
        'recommendation': 'Never use exec() on user input. Restructure code to avoid dynamic execution',
    },
    'os_system': {
        'pattern': re.compile(r'\bos\.system\s*\('),
        'severity': 'high',
        'message': 'os.system() executes shell commands - injection risk',
        'recommendation': 'Use subprocess.run() with list args instead of shell=True',
    },
    'subprocess_shell': {
        'pattern': re.compile(r'subprocess\.\w+\s*\(.*shell\s*=\s*True'),
        'severity': 'high',
        'message': 'subprocess with shell=True - command injection risk',
        'recommendation': 'Use shell=False with list args to prevent shell injection',
    },
    'format_disk': {
        'pattern': re.compile(r'\bformat\s+/|\bdd\s+if=|\bmke2fs\b|\bmkfs\.', re.IGNORECASE),
        'severity': 'critical',
        'message': 'Disk formatting/destructive storage operation detected',
        'recommendation': 'This is extremely dangerous. Require explicit user confirmation with typed confirmation',
    },
    'wildcard_delete': {
        'pattern': re.compile(r'\bdel\s+/[fq]\s+.*\*|\brm\s+.*\*\s+--no-preserve-root'),
        'severity': 'critical',
        'message': 'Wildcard file deletion detected',
        'recommendation': 'Explicitly list files to delete, validate paths, and require confirmation',
    },
}


# ───────────────────────────────────────────────
# Internal Helpers
# ───────────────────────────────────────────────


def _calculate_entropy(string: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not string:
        return 0.0
    prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
    return -sum(p * math.log2(p) for p in prob)


def _check_secret_assignments(tree: ast.AST, findings: List[Dict]):
    """AST-based check for secret variable assignments."""
    secret_var_patterns = re.compile(r'(?i)(api_key|secret|token|password|passwd|auth)')

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if secret_var_patterns.search(target.id):
                        # Check if assigned value is a string literal
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            val = node.value.value
                            if len(val) >= 8:
                                entropy = _calculate_entropy(val)
                                if entropy >= 4.0:
                                    # Avoid duplicate if already found by regex
                                    if not any(f['line'] == node.lineno for f in findings):
                                        findings.append({
                                            'line': node.lineno,
                                            'type': 'hardcoded_secret',
                                            'subtype': 'secret_assignment',
                                            'severity': 'critical',
                                            'evidence': f'{target.id} = "..."',
                                            'entropy': round(entropy, 2),
                                            'message': f"Hardcoded secret in variable '{target.id}' (entropy={entropy:.2f})",
                                        })


class _SQLInjectionVisitor(ast.NodeVisitor):
    """AST visitor for detecting SQL injection in Python code."""

    SQL_METHODS = {'execute', 'executemany', 'executescript', 'query', 'raw'}

    def __init__(self):
        self.findings: List[Dict] = []
        self.var_assignments: Dict[str, ast.AST] = {}

    def visit_FunctionDef(self, node):
        self.var_assignments = {}
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.var_assignments[target.id] = node.value
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = self._get_func_name(node.func)
        if func_name and any(sql in func_name.lower() for sql in self.SQL_METHODS):
            if node.args:
                arg = node.args[0]
                self._check_arg(node, arg, func_name)
        self.generic_visit(node)

    def _check_arg(self, call_node, arg, func_name):
        """Check if an argument is potentially injectable."""
        # Direct string concatenation
        if isinstance(arg, ast.BinOp):
            if isinstance(arg.op, (ast.Add,)):
                self.findings.append({
                    'line': call_node.lineno,
                    'type': 'sql_injection',
                    'subtype': 'ast_string_concat',
                    'severity': 'critical',
                    'evidence': f'{func_name}(...) with string concatenation',
                    'message': f'Potential SQL injection in {func_name}() via string concatenation',
                    'fix': 'Use parameterized queries with placeholder arguments',
                })
            return

        # f-string
        if isinstance(arg, ast.JoinedStr):
            self.findings.append({
                'line': call_node.lineno,
                'type': 'sql_injection',
                'subtype': 'ast_f_string',
                'severity': 'critical',
                'evidence': f'{func_name}(...) with f-string',
                'message': f'Potential SQL injection in {func_name}() via f-string interpolation',
                'fix': 'Use parameterized queries instead of f-strings for SQL',
            })
            return

        # .format() call
        if isinstance(arg, ast.Call):
            if isinstance(arg.func, ast.Attribute) and arg.func.attr == 'format':
                self.findings.append({
                    'line': call_node.lineno,
                    'type': 'sql_injection',
                    'subtype': 'ast_format_method',
                    'severity': 'critical',
                    'evidence': f'{func_name}(...) with .format()',
                    'message': f'Potential SQL injection in {func_name}() via .format()',
                    'fix': 'Use parameterized queries instead',
                })
            return

        # Variable reference — trace back to its assignment
        if isinstance(arg, ast.Name):
            assigned_value = self.var_assignments.get(arg.id)
            if assigned_value:
                self._check_arg(call_node, assigned_value, func_name)
            return

    def _get_func_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return ''


# ───────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Security Scanner - Lightweight security pattern detection')
    subparsers = parser.add_subparsers(dest='command', required=True)

    p = subparsers.add_parser('secrets', help='Scan for hardcoded secrets')
    p.add_argument('--file', required=True)

    p = subparsers.add_parser('sql_injection', help='Scan for SQL injection patterns')
    p.add_argument('--file', required=True)

    p = subparsers.add_parser('xss', help='Scan for XSS vectors')
    p.add_argument('--file', required=True)

    p = subparsers.add_parser('misconfig', help='Scan for dangerous configurations')
    p.add_argument('--file', required=True)

    p = subparsers.add_parser('dangerous_ops', help='Scan content for dangerous operations')
    p.add_argument('--content', required=True, help='Content string to scan (or use --file)')

    p = subparsers.add_parser('all', help='Run all scans on a file')
    p.add_argument('--file', required=True)

    args = parser.parse_args()

    if args.command == 'secrets':
        result = scan_secrets(args.file)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'sql_injection':
        result = scan_sql_injection(args.file)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'xss':
        result = scan_xss_vectors(args.file)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'misconfig':
        result = scan_misconfiguration(args.file)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'dangerous_ops':
        result = scan_dangerous_operations(args.content)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == 'all':
        result = {
            'secrets': scan_secrets(args.file),
            'sql_injection': scan_sql_injection(args.file),
            'xss': scan_xss_vectors(args.file),
            'misconfiguration': scan_misconfiguration(args.file),
        }
        print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
