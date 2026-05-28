"""Security Auditor - Bridge between YangJian's security_audit domain
and WangLingGuan's security_scanner engine.

Imports the existing scanner, runs all scan types, and formats
output in YangJian's [security_audit] + [boundary_checks] schema.
"""

import os
import sys
from typing import Dict, List, Optional

# Ensure project root is on path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from skills.tool_wanglingguan.scripts.security_scanner import (
    scan_secrets,
    scan_sql_injection,
    scan_xss_vectors,
    scan_misconfiguration,
    scan_dangerous_operations,
)

# Severity ranking for sorting
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _normalize_severity(raw: str) -> str:
    """Map scanner severity strings to YangJian schema levels."""
    mapping = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }
    return mapping.get(raw.lower(), "Medium")


def _finding_to_boundary_check(finding: dict, counter: list) -> Optional[dict]:
    """Convert a scanner finding to a [boundary_checks] entry."""
    if "error" in finding:
        return None

    ftype = finding.get("type", "UNKNOWN")
    boundary_type_map = {
        "hardcoded_secret": "INFO_EXPOSURE",
        "sql_injection": "INPUT_VALIDATION",
        "xss_vector": "INPUT_VALIDATION",
        "debug_enabled": "REGISTRATION",
        "dangerous_default": "REGISTRATION",
        "dangerous_call": "NULL_PATH",
    }
    bc_type = boundary_type_map.get(ftype, "INPUT_VALIDATION")

    counter[0] += 1
    return {
        "id": f"BC-{counter[0]:03d}",
        "type": bc_type,
        "location": f"{finding.get('file', 'unknown')}:{finding.get('line', '?')}",
        "description": finding.get("evidence", finding.get("pattern", ftype)),
        "concern": finding.get("detail", ftype),
        "verification_needed": f"Verify {ftype} at line {finding.get('line', '?')}",
    }


def _finding_to_audit_entry(finding: dict, counter: list) -> Optional[dict]:
    """Convert a scanner finding to a [security_audit] entry."""
    if "error" in finding:
        return None

    counter[0] += 1
    return {
        "id": f"SA-{counter[0]:03d}",
        "severity": _normalize_severity(finding.get("severity", "medium")),
        "location": f"{finding.get('file', 'unknown')}:{finding.get('line', '?')}",
        "issue": finding.get("type", "unknown"),
        "impact": finding.get("detail", finding.get("pattern", "")),
        "recommendation": finding.get("fix", "Review and remediate this finding."),
    }


def run_security_audit(target: str, is_content: bool = False) -> str:
    """Run full security audit on a file or code content.

    Args:
        target: File path, or raw code content if is_content=True.
        is_content: If True, treat target as code string (skip file-based scans).

    Returns:
        Structured report in YangJian's [security_audit] + [boundary_checks] format.
    """
    all_findings: List[dict] = []

    if is_content:
        # Only content-based scan is available
        findings = scan_dangerous_operations(target)
        for f in findings:
            f.setdefault("file", "<content>")
        all_findings.extend(findings)
        file_label = "<content>"
    else:
        if not os.path.exists(target):
            return (
                "[task_status]: failed\n"
                f"[output_summary]: Target file not found: {target}\n"
                "[capability_used]: security_audit\n"
                "[tags]: security, error\n"
            )
        file_label = target
        for scan_fn in [scan_secrets, scan_sql_injection, scan_xss_vectors, scan_misconfiguration]:
            findings = scan_fn(target)
            for f in findings:
                f.setdefault("file", target)
            all_findings.extend(findings)
        # Also scan content-based patterns
        try:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            findings = scan_dangerous_operations(content)
            for f in findings:
                f.setdefault("file", target)
            all_findings.extend(findings)
        except Exception:
            pass

    # Filter out error entries
    valid_findings = [f for f in all_findings if "error" not in f]

    # Build structured output
    bc_counter = [0]
    sa_counter = [0]
    boundary_checks = []
    audit_entries = []

    for finding in valid_findings:
        bc = _finding_to_boundary_check(finding, bc_counter)
        if bc:
            boundary_checks.append(bc)
        sa = _finding_to_audit_entry(finding, sa_counter)
        if sa:
            audit_entries.append(sa)

    # Sort by severity
    audit_entries.sort(key=lambda e: _SEVERITY_ORDER.get(e["severity"].lower(), 99))

    # Count by severity
    severity_counts: Dict[str, int] = {}
    for e in audit_entries:
        sev = e["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Build report
    sections = []
    sections.append("[task_status]: completed")
    sections.append(
        f"[output_summary]: Security scan of {file_label} found "
        f"{len(audit_entries)} issue(s) — "
        + ", ".join(f"{v} {k}" for k, v in sorted(severity_counts.items()))
        if audit_entries
        else f"[output_summary]: Security scan of {file_label} found no issues"
    )
    sections.append("[capability_used]: security_audit")
    sections.append("[tags]: security, audit, boundary")

    # Security audit entries
    if audit_entries:
        sections.append("")
        sections.append("[security_audit]:")
        for entry in audit_entries:
            sections.append(f"  - id: {entry['id']}")
            sections.append(f"    severity: {entry['severity']}")
            sections.append(f"    location: {entry['location']}")
            sections.append(f"    issue: {entry['issue']}")
            sections.append(f"    impact: {entry['impact']}")
            sections.append(f"    recommendation: {entry['recommendation']}")
            sections.append("")

    # Boundary checks
    if boundary_checks:
        sections.append("[boundary_checks]:")
        for bc in boundary_checks:
            sections.append(f"  - id: {bc['id']}")
            sections.append(f"    type: {bc['type']}")
            sections.append(f"    location: {bc['location']}")
            sections.append(f"    description: {bc['description']}")
            sections.append(f"    concern: {bc['concern']}")
            sections.append(f"    verification_needed: {bc['verification_needed']}")
            sections.append("")

    # Routing recommendation
    if audit_entries:
        critical = severity_counts.get("Critical", 0)
        high = severity_counts.get("High", 0)
        if critical > 0:
            sections.append("[next_action]: capability: problem_solving, tags: [debug, fix, security, critical]")
        elif high > 0:
            sections.append("[next_action]: capability: problem_solving, tags: [debug, fix, security]")
        else:
            sections.append("[next_action]: capability: problem_solving, tags: [fix, security, low_priority]")
    else:
        sections.append("[next_action]: No security issues found. Code appears safe.")

    return "\n".join(sections)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YangJian Security Auditor")
    parser.add_argument("target", help="File path to scan")
    parser.add_argument("--content", action="store_true", help="Treat target as raw code string")
    args = parser.parse_args()
    print(run_security_audit(args.target, is_content=args.content))
