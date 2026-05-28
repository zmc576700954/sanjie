"""Weighted confidence scorer for error classification results."""
from skills.tool_bajiu.scripts.text_utils import word_match

# Weighted keyword maps: higher weight = more specific/diagnostic keyword
KEYWORD_WEIGHTS = {
    "yindan": {
        "none": 2.0, "typeerror": 2.0, "null": 1.8, "attribute": 1.5,
        "import": 1.5, "module": 1.0,
    },
    "sanjian": {
        "refactor": 2.0, "rewrite": 2.0, "restructure": 1.8,
        "重构": 2.0, "重写": 2.0,
    },
    "kaishan": {
        "bulk": 2.0, "cleanup": 1.8, "deprecated": 1.5,
        "批量": 2.0, "清理": 1.8, "废弃": 1.5,
    },
    "taie": {
        "feature": 2.0, "implement": 1.8, "add": 1.5,
        "新增": 2.0, "开发": 1.8, "实现": 1.5,
    },
}


def score_classification(result: dict, error_desc: str) -> float:
    """Score classification confidence using weighted keyword matching.
    Returns a float between 0.0 and 1.0."""
    recommended_skill = result.get("recommended_skill", "")
    weights = KEYWORD_WEIGHTS.get(recommended_skill, {})

    if not weights:
        return 0.5

    total_weight = sum(weights.values())
    matched_weight = 0.0

    for kw, weight in weights.items():
        if word_match(error_desc, [kw]):
            matched_weight += weight

    if total_weight == 0:
        return 0.5

    raw_score = matched_weight / total_weight

    # Map to threshold-friendly values:
    # 0 matched -> 0.5 (no signal)
    # partial match -> 0.7 (some signal)
    # strong match (>=60% weight) -> 0.9 (high signal)
    if matched_weight == 0:
        return 0.5
    elif raw_score >= 0.6:
        return 0.9
    else:
        return 0.7
