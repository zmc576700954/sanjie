"""Unified classification engine used by both task_analyzer and route_orchestrator.
Provides a single source of truth for skill matching logic."""
from skills.tool_bajiu.scripts.text_utils import word_match, score_keywords

# ── Skill definitions with weighted keywords ──

SKILL_KEYWORDS = {
    "yindan": {
        "keywords": ["none", "typeerror", "import", "module", "null", "attribute",
                      "fix", "repair", "patch", "修复", "修正", "替换"],
        "weights": {
            "none": 2.0, "typeerror": 2.0, "null": 1.8, "attribute": 1.5,
            "import": 1.5, "module": 1.0,
            "fix": 1.5, "repair": 1.5, "patch": 1.5,
            "修复": 1.5, "修正": 1.5, "替换": 1.5,
        },
    },
    "sanjian": {
        "keywords": ["refactor", "rewrite", "restructure", "重构", "重写", "重组"],
        "weights": {
            "refactor": 2.0, "rewrite": 2.0, "restructure": 1.8,
            "重构": 2.0, "重写": 2.0, "重组": 1.8,
        },
    },
    "kaishan": {
        "keywords": ["bulk", "cleanup", "deprecated", "批量", "清理", "废弃"],
        "weights": {
            "bulk": 2.0, "cleanup": 1.8, "deprecated": 1.5,
            "批量": 2.0, "清理": 1.8, "废弃": 1.5,
        },
    },
    "taie": {
        "keywords": ["feature", "implement", "add", "新增", "开发", "实现"],
        "weights": {
            "feature": 2.0, "implement": 1.8, "add": 1.5,
            "新增": 2.0, "开发": 1.8, "实现": 1.5,
        },
    },
}

# Ordered priority for disambiguation when scores tie
SKILL_PRIORITY = ["sanjian", "kaishan", "taie", "yindan"]


def classify(text: str) -> dict:
    """Classify text into one of the four skills using weighted keyword matching.
    Returns: {recommended_skill, confidence, tier, reasoning, scores}"""
    scores = {}
    for skill_name, config in SKILL_KEYWORDS.items():
        score = score_keywords(text, config["weights"])
        scores[skill_name] = round(score, 3)

    # Pick highest score; break ties by priority order
    best_skill = None
    best_score = 0.0
    for skill in SKILL_PRIORITY:
        if scores[skill] > best_score:
            best_score = scores[skill]
            best_skill = skill

    # Fallback: if no keyword matched at all, default to yindan
    if best_score == 0.0:
        best_skill = "yindan"
        best_score = 0.0

    # Determine tier based on confidence
    if best_score >= 0.5:
        tier = "L1"
        confidence = "high"
    elif best_score > 0.0:
        tier = "L1"
        confidence = "medium"
    else:
        tier = "L3"
        confidence = "low"

    reasoning_parts = [f"{s}={scores[s]:.2f}" for s in SKILL_PRIORITY if scores[s] > 0]
    reasoning = f"Weighted classification: {', '.join(reasoning_parts)}" if reasoning_parts else "No keyword match"

    return {
        "recommended_skill": best_skill,
        "confidence": confidence,
        "tier": tier,
        "reasoning": reasoning,
        "scores": scores,
        "score_value": best_score,
    }


def classify_with_context(text: str, root_cause: str = "", logic_chain: str = "", action: str = "") -> dict:
    """Classify and merge with optional context fields for route_orchestrator compatibility."""
    result = classify(text)
    result["root_cause"] = root_cause or "Auto-classified by unified engine."
    result["logic_chain"] = logic_chain or f"Error: {text[:80]}."
    result["action"] = action or "Apply classified skill."
    return result
