"""Decompose refactoring tasks into ordered subtasks."""
import os
import re
from typing import List, Optional


# ── Matching rules ────────────────────────────────────────────────────────────
# Three-layer matching: phrases (confidence=1.0) -> keywords (0.8) -> default (0.0)
# CJK keywords use plain substring matching (Python \b does not work on non-ASCII).
# Short ASCII keywords (len<=3) use \b word boundary to avoid false positives.

_OPERATION_RULES = [
    {
        "type": "REWRITE",
        "keywords": [
            "rewrite", "overhaul", "rebuild", "redo",
            "completely replace", "start from scratch", "scrap",
            "重写", "彻底", "颠覆", "推翻重来",
            "从头写", "全部重做", "完全重写",
            "推倒重来", "重做", "从头开始",
        ],
        "phrases": [
            "rewrite the whole", "rewrite everything", "start over",
            "completely replace", "replace entirely", "nuke and rewrite",
            "from scratch", "needs to be redone",
            "needs to be completely rebuilt", "needs rewriting",
            "完全重写", "推翻重来", "从头写", "完全重做",
        ],
    },
    {
        "type": "INTEGRATE",
        "keywords": [
            "integrate", "merge", "unify", "combine", "consolidate",
            "absorb", "fold into", "bring together", "join",
            "整合", "合并", "统一", "融合",
            "合到一起", "归并", "合并到",
            "合在一起", "汇集", "合到一块",
        ],
        "phrases": [
            "put together", "merge into one", "combine into",
            "fold into one", "fold these", "fold the",
            "bring together", "should be merged",
            "these files should be merged",
            "把这两个合", "合到一起", "归并成一个",
        ],
    },
    {
        "type": "RESTRUCTURE",
        "keywords": [
            "restructure", "reorganize", "refactor", "clean up", "cleanup",
            "simplify", "decouple", "split", "separate", "extract",
            "move", "rearrange", "tidy", "modularize", "encapsulate",
            "重构", "整理", "拆分", "解耦",
            "分离", "抽取", "提取", "抽",
            "调整结构", "优化结构",
            "模块化", "封装", "拆开",
            "清理", "简化",
        ],
        "phrases": [
            "clean up the code", "make it cleaner", "too messy",
            "break it down", "split apart", "move to separate",
            "needs reorganizing", "needs to be restructured",
            "代码太乱", "拆成多个",
            "分成多个", "太乱了",
            "做的事情太多",
        ],
    },
]

_SCOPE_RULES = [
    {
        "level": "DEEP",
        "keywords": [
            "cross-module", "global", "system-wide", "architectural",
            "foundational", "across all modules",
            "跨模块", "全局", "底层",
            "全面", "整体", "架构", "基础",
        ],
        "phrases": [
            "across all modules", "affects everything", "system wide",
            "all modules", "throughout the codebase",
            "影响所有模块", "所有模块都要改",
        ],
    },
    {
        "level": "BOUNDARY",
        "keywords": [
            "interface", "dependency", "api", "contract", "boundary",
            "public", "export", "external",
            "接口", "依赖", "对外", "暴露",
        ],
        "phrases": [
            "public interface", "breaking change", "api contract",
            "对外接口", "公共接口", "接口需要",
        ],
    },
]


def _normalize(text: str) -> str:
    """Lowercase and collapse whitespace for matching."""
    return re.sub(r'\s+', ' ', text.lower().strip())


def _match_rule(rules: list, text: str, default: str) -> tuple:
    """
    Match text against rules using three-layer strategy.
    Returns (matched_value, confidence, matched_keyword).
    """
    norm = _normalize(text)
    value_key = "type" if "type" in rules[0] else "level"

    # Phase 1: phrase match (highest confidence)
    for rule in rules:
        for phrase in rule.get("phrases", []):
            if phrase.lower() in norm:
                return (rule[value_key], 1.0, phrase)

    # Phase 2: keyword match
    for rule in rules:
        for kw in rule.get("keywords", []):
            kw_lower = kw.lower()
            if kw_lower in norm:
                # Short ASCII keywords need \b to avoid false positives
                # (e.g. "fix" matching "prefix"). CJK chars don't work with
                # \b so we use plain substring for non-ASCII.
                if len(kw) <= 3 and kw.isascii():
                    pattern = r'\b' + re.escape(kw_lower) + r'\b'
                    if re.search(pattern, norm):
                        return (rule[value_key], 0.8, kw)
                else:
                    return (rule[value_key], 0.8, kw)

    return (default, 0.0, "")


def decompose(task_context: str, target_files: List[str],
              dependency_graph: Optional[dict] = None) -> dict:
    """
    Split a refactoring task into subtasks with dependency ordering.

    Args:
        task_context: Description of what needs to be refactored
        target_files: List of file paths to operate on
        dependency_graph: Optional output from analyze_dependencies().
            If provided, used to build real DAG dependencies between subtasks
            instead of a simple sequential chain.

    Returns:
        {subtasks, execution_order, summary, match_info}
    """
    operation, op_conf, op_keyword = _match_rule(
        _OPERATION_RULES, task_context, "RESTRUCTURE"
    )
    scope_level, sc_conf, sc_keyword = _match_rule(
        _SCOPE_RULES, task_context, "SAFE"
    )

    # Build file-to-index mapping for dependency resolution
    file_to_idx = {f: i for i, f in enumerate(target_files)}

    subtasks = []
    for idx, filepath in enumerate(target_files):
        subtask_id = "subtask_%d" % (idx + 1)

        # Determine dependencies
        if dependency_graph and filepath in dependency_graph:
            # Use real dependency graph: depend on files that this file imports
            deps = []
            for dep_file in dependency_graph[filepath]:
                if dep_file in file_to_idx:
                    deps.append("subtask_%d" % (file_to_idx[dep_file] + 1))
        elif idx > 0:
            # Fallback: sequential chain
            deps = ["subtask_%d" % idx]
        else:
            deps = []

        subtasks.append({
            "id": subtask_id,
            "target_file": filepath,
            "operation": operation,
            "description": "%s on %s" % (operation, os.path.basename(filepath)),
            "dependencies": deps,
            "scope_level": scope_level,
        })

    execution_order = [s["id"] for s in subtasks]

    return {
        "subtasks": subtasks,
        "execution_order": execution_order,
        "summary": "Decomposed into %d subtasks, operation: %s" % (len(subtasks), operation),
        "match_info": {
            "operation": {"value": operation, "confidence": op_conf, "matched_by": op_keyword},
            "scope": {"value": scope_level, "confidence": sc_conf, "matched_by": sc_keyword},
            "needs_ai_fallback": op_conf == 0.0 and sc_conf == 0.0,
        },
    }
