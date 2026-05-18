KEYWORD_MAP = {
    "yindan": ["none", "typeerror", "import", "module", "null", "attribute"],
    "sanjian": ["refactor", "rewrite", "restructure", "重构", "重写"],
    "kaishan": ["bulk", "cleanup", "deprecated", "批量", "清理", "废弃"],
    "taie": ["feature", "implement", "add", "新增", "开发", "实现"],
}


def score_classification(result: dict, error_desc: str) -> float:
    """Score classification confidence based on keyword matches in error_desc."""
    recommended_skill = result.get("recommended_skill", "")
    keywords = KEYWORD_MAP.get(recommended_skill, [])

    error_lower = error_desc.lower()
    hit_count = sum(1 for kw in keywords if kw.lower() in error_lower)

    if hit_count >= 2:
        return 0.9
    elif hit_count == 1:
        return 0.7
    else:
        return 0.5
