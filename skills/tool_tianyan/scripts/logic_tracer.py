"""Error investigation and logic tracing."""
import os
import re
from typing import Optional

from skills.tool_bajiu.scripts.keyword_router import classify_error


def trace_error(error_desc: str, log_file: Optional[str] = None, source_code_context: str = "") -> str:
    """
    Analyze error and generate structured handoff report.

    Args:
        error_desc: Description of the error
        log_file: Optional path to log file
        source_code_context: Optional source code snippet

    Returns:
        Structured handoff report string
    """
    sections = []

    # Phase 1: Log analysis — read last ~500 chars without loading entire file
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                file_size = f.seek(0, os.SEEK_END)
                start = max(0, file_size - 1500)
                f.seek(start)
                # Discard potential partial first character
                if start > 0:
                    f.read(1)
                log_tail = f.read()[-500:]
            sections.append(f"[log_excerpt]: ...{log_tail}")
        except Exception:
            sections.append("[log_excerpt]: Unable to read log file.")

    # Phase 2: Error classification
    analysis = classify_error(error_desc)

    # Phase 3: Handoff report
    report = (
        f"[logic_chain]: {analysis['logic_chain']}\n"
        f"[root_cause]: {analysis['root_cause']}\n"
        f"[recommended_skill]: {analysis['recommended_skill']}\n"
        f"[action]: {analysis['action']}"
    )
    sections.append(report)

    return "\n".join(sections)


