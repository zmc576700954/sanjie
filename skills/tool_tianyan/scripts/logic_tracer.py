"""Error investigation and logic tracing."""
import os
import re
from typing import Optional

from skills.tool_bajiu.scripts.keyword_router import classify_error


def _extract_context_hints(source_code_context, detected_type):
    if not source_code_context:
        return ""
    lines = source_code_context.splitlines()
    hints = []
    patterns = {
        "NoneType":    [r"\bNone\b", r"\.get\(", r"return\s*$"],
        "ImportError": [r"^\s*import\b", r"^\s*from\b"],
        "KeyError":    [r"\[[\"']", r"\.get\("],
        "TypeError":   [r"str\(", r"int\(", r"float\(", r"bool\("],
        "AttributeError": [r"\.\w+\("],
    }
    search_pats = patterns.get(detected_type)
    if search_pats is None:
        # Generic fallback: look for common risky patterns
        search_pats = [
            r"\bNone\b", r"\bnull\b",
            r"^\s*import\b", r"^\s*from\b",
            r"\.get\(", r"\.\w+\(",
        ]
    for i, line in enumerate(lines, 1):
        for pat in search_pats:
            if re.search(pat, line):
                hints.append("  line %d: %s" % (i, line.rstrip()))
                break
    if not hints:
        return ""
    return "Relevant lines from source context:\n" + "\n".join(hints[:10])


def trace_error(error_desc, log_file=None, source_code_context=""):
    sections = []

    # Phase 1: Log analysis
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                file_size = f.seek(0, os.SEEK_END)
                if file_size == 0:
                    sections.append("[log_excerpt]: <log file is empty>")
                else:
                    start = max(0, file_size - 1500)
                    f.seek(start)
                    if start > 0:
                        f.read(1)
                    log_tail = f.read()[-500:]
                    sections.append("[log_excerpt]: ...%s" % log_tail)
        except Exception:
            sections.append("[log_excerpt]: Unable to read log file.")

    # Phase 2: Error classification (context-aware)
    analysis = classify_error(error_desc, source_code_context=source_code_context)

    # Phase 3: Context hints
    context_hints = _extract_context_hints(
        source_code_context, analysis.get("detected_error_type", "")
    )
    if context_hints:
        sections.append("[source_context_hints]:\n%s" % context_hints)

    # Phase 4: Handoff report
    report = (
        "[logic_chain]: %s\n"
        "[root_cause]: %s\n"
        "[recommended_skill]: %s\n"
        "[action]: %s"
    ) % (analysis['logic_chain'], analysis['root_cause'],
         analysis['recommended_skill'], analysis['action'])

    if analysis.get("confidence"):
        report += "\n[confidence]: %s" % analysis['confidence']
    if analysis.get("error_detail"):
        report += "\n[error_detail]: %s" % analysis['error_detail']
    if analysis.get("detected_error_type"):
        report += "\n[detected_error_type]: %s" % analysis['detected_error_type']

    sections.append(report)
    return "\n".join(sections)
