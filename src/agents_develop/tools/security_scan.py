"""Wrappers for security scanning tools from skills/."""
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from skills.tool_wanglingguan.scripts.security_scanner import (
    scan_secrets as _scan_secrets,
    scan_sql_injection as _scan_sql_injection,
    scan_xss_vectors as _scan_xss_vectors,
    scan_misconfiguration as _scan_misconfig,
)


def scan_secrets(file_path: str) -> list[dict]:
    """Scan for hardcoded secrets, API keys, tokens."""
    return _scan_secrets(file_path)


def scan_sql_injection(file_path: str) -> list[dict]:
    """Scan for SQL injection patterns."""
    return _scan_sql_injection(file_path)


def scan_xss(file_path: str) -> list[dict]:
    """Scan for XSS vectors."""
    return _scan_xss_vectors(file_path)


def scan_misconfiguration(file_path: str) -> list[dict]:
    """Scan for dangerous configurations."""
    return _scan_misconfig(file_path)


def scan_file(file_path: str, scan_types: list[str] = None) -> list[dict]:
    """Run selected security scans on a file."""
    if scan_types is None:
        scan_types = ["secrets", "sql_injection", "xss", "misconfiguration"]

    findings = []
    scanners = {
        "secrets": _scan_secrets,
        "sql_injection": _scan_sql_injection,
        "xss": _scan_xss_vectors,
        "misconfiguration": _scan_misconfig,
    }
    for stype in scan_types:
        if stype in scanners:
            findings.extend(scanners[stype](file_path))
    return findings


def scan_all(file_path: str) -> list[dict]:
    """Run all security scans on a file."""
    return scan_file(file_path)
