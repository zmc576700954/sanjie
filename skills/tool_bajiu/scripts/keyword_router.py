"""Keyword router for classifying errors and recommending downstream skills."""


def classify_error(error_desc: str) -> dict:
    """Classify error type and recommend downstream skill."""
    desc_lower = error_desc.lower()

    if "none" in desc_lower or "typeerror" in desc_lower:
        return {
            "logic_chain": "Method returns None when input not found in data source.",
            "root_cause": "Missing null check — accessing attribute on None value.",
            "recommended_skill": "yindan",
            "action": "Add None guard with appropriate default return value.",
        }

    if any(k in error_desc for k in ["refactor", "rewrite", "restructure", "重构", "重写"]):
        return {
            "logic_chain": "Current architecture cannot support required changes.",
            "root_cause": "Structural design limitation requiring multi-file rework.",
            "recommended_skill": "sanjian",
            "action": "Decompose into subtasks and execute with scope control.",
        }

    if any(k in error_desc for k in ["bulk", "cleanup", "deprecated", "批量", "清理", "废弃"]):
        return {
            "logic_chain": "Accumulated dead code affecting maintainability.",
            "root_cause": "Legacy code not removed during previous iterations.",
            "recommended_skill": "kaishan",
            "action": "Define pattern, assess blast radius, execute with logging.",
        }

    if any(k in error_desc for k in ["feature", "implement", "add", "新增", "开发", "实现"]):
        return {
            "logic_chain": "Missing functionality requested by user.",
            "root_cause": "Feature not yet implemented.",
            "recommended_skill": "taie",
            "action": "Develop feature with risk assessment and regression validation.",
        }

    if "import" in desc_lower or "module" in desc_lower:
        return {
            "logic_chain": "Code references unavailable module.",
            "root_cause": "Import path incorrect or dependency missing.",
            "recommended_skill": "yindan",
            "action": "Fix import path or add missing dependency declaration.",
        }

    return {
        "logic_chain": f"Error: {error_desc[:80]}. Requires further context.",
        "root_cause": "Insufficient information for definitive classification.",
        "recommended_skill": "yindan",
        "action": "Gather more context, then apply minimal fix.",
    }
