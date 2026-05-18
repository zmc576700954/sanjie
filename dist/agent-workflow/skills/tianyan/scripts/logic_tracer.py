"""Error investigation and logic tracing."""
import os
import re
from typing import Optional


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

    # Phase 1: Log analysis
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_tail = f.read()[-500:]
            sections.append(f"[log_excerpt]: ...{log_tail}")
        except Exception:
            sections.append("[log_excerpt]: Unable to read log file.")

    # Phase 2: Error classification
    analysis = _classify_error(error_desc, source_code_context)

    # Phase 3: Handoff report
    report = (
        f"[logic_chain]: {analysis['logic_chain']}\n"
        f"[root_cause]: {analysis['root_cause']}\n"
        f"[recommended_skill]: {analysis['recommended_skill']}\n"
        f"[action]: {analysis['action']}"
    )
    sections.append(report)

    return "\n".join(sections)


def _classify_error(error_desc: str, source_code_context: str) -> dict:
    """Classify error type and recommend downstream skill."""
    desc_lower = error_desc.lower()

    # NoneType / TypeError
    if "none" in desc_lower or "typeerror" in desc_lower:
        return {
            "logic_chain": "Method returns None when input not found in data source.",
            "root_cause": "Missing null check — accessing attribute on None value.",
            "recommended_skill": "yindan",
            "action": "Add None guard with appropriate default return value.",
        }

    # Refactoring needed
    if any(k in error_desc for k in ["refactor", "rewrite", "restructure", "重构", "重写"]):
        return {
            "logic_chain": "Current architecture cannot support required changes.",
            "root_cause": "Structural design limitation requiring multi-file rework.",
            "recommended_skill": "sanjian",
            "action": "Decompose into subtasks and execute with scope control.",
        }

    # Bulk cleanup
    if any(k in error_desc for k in ["bulk", "cleanup", "deprecated", "批量", "清理", "废弃"]):
        return {
            "logic_chain": "Accumulated dead code affecting maintainability.",
            "root_cause": "Legacy code not removed during previous iterations.",
            "recommended_skill": "kaishan",
            "action": "Define pattern, assess blast radius, execute with logging.",
        }

    # Feature development
    if any(k in error_desc for k in ["feature", "implement", "add", "新增", "开发", "实现"]):
        return {
            "logic_chain": "Missing functionality requested by user.",
            "root_cause": "Feature not yet implemented.",
            "recommended_skill": "taie",
            "action": "Develop feature with risk assessment and regression validation.",
        }

    # Import / Module errors
    if "import" in desc_lower or "module" in desc_lower:
        return {
            "logic_chain": "Code references unavailable module.",
            "root_cause": "Import path incorrect or dependency missing.",
            "recommended_skill": "yindan",
            "action": "Fix import path or add missing dependency declaration.",
        }

    # Default
    return {
        "logic_chain": f"Error: {error_desc[:80]}. Requires further context.",
        "root_cause": "Insufficient information for definitive classification.",
        "recommended_skill": "yindan",
        "action": "Gather more context, then apply minimal fix.",
    }
