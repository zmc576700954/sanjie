"""Three-tier routing orchestrator: L1 keyword, L2 local/LLM, L3 fallback."""

import json

from skills.tool_bajiu.scripts import keyword_router
from skills.tool_bajiu.scripts import confidence_scorer
from skills.tool_bajiu.scripts.unified_classifier import classify as unified_classify
from skills.tool_bajiu.scripts.providers import get_available_provider


SKILL_OPTIONS = ["yindan", "sanjian", "kaishan", "taie"]


def build_system_prompt() -> str:
    """Return a prompt instructing the LLM to classify errors into one of the four skills."""
    return (
        "You are an error classifier for a software repair system. "
        "Classify the given error into exactly one of these skills: "
        f"{', '.join(SKILL_OPTIONS)}. "
        "Output ONLY a JSON object with this exact schema:\n"
        '{"recommended_skill": "<one of yindan/sanjian/kaishan/taie>", '
        '"confidence": <float 0.0-1.0>, '
        '"reasoning": "<brief explanation>"}\n'
        "Do not include any other text."
    )


def _ensure_keys(result: dict, error_desc: str) -> dict:
    """Ensure the result dict contains all required keys."""
    defaults = {
        "recommended_skill": "yindan",
        "root_cause": "Unknown root cause.",
        "logic_chain": f"Error: {error_desc[:80]}.",
        "action": "Investigate and apply minimal fix.",
        "confidence": "low",
        "reasoning": "Fallback classification.",
        "tier": "L3",
    }
    for key, value in defaults.items():
        if key not in result:
            result[key] = value
    return result


def route(error_desc: str, source_code: str = "") -> dict:
    """Route an error through L1 -> L2 -> L3 tiers and return a classification dict."""
    # L1: keyword-based classification
    l1_result = keyword_router.classify_error(error_desc)

    # L1 confidence scoring
    confidence_value = confidence_scorer.score_classification(l1_result, error_desc)

    if confidence_value >= 0.7:
        result = dict(l1_result)
        result["confidence"] = "high"
        result["tier"] = "L1"
        result["reasoning"] = f"L1 keyword match with confidence {confidence_value:.2f}"
        return _ensure_keys(result, error_desc)

    # L2: try LLM first, then local unified classifier as fallback
    provider = get_available_provider()
    if provider is not None:
        try:
            system_prompt = build_system_prompt()
            llm_output = provider.infer(system_prompt, error_desc, timeout=5.0)
            parsed = json.loads(llm_output)

            if parsed.get("confidence", 0.0) >= 0.6:
                result = {
                    "recommended_skill": parsed.get("recommended_skill", l1_result.get("recommended_skill", "yindan")),
                    "root_cause": l1_result.get("root_cause", "Unknown root cause."),
                    "logic_chain": l1_result.get("logic_chain", f"Error: {error_desc[:80]}."),
                    "action": l1_result.get("action", "Investigate and apply minimal fix."),
                    "confidence": "medium",
                    "reasoning": parsed.get("reasoning", "L2 LLM classification."),
                    "tier": "L2",
                }
                return _ensure_keys(result, error_desc)
        except Exception:
            pass

    # L2 fallback: local unified classifier (no LLM required)
    local_result = unified_classify(error_desc)
    if local_result["score_value"] > 0:
        result = {
            "recommended_skill": local_result["recommended_skill"],
            "root_cause": l1_result.get("root_cause", "Classified by local engine."),
            "logic_chain": l1_result.get("logic_chain", f"Error: {error_desc[:80]}."),
            "action": l1_result.get("action", "Apply classified skill."),
            "confidence": "medium",
            "reasoning": f"L2 local classifier: {local_result['reasoning']}",
            "tier": "L2",
        }
        return _ensure_keys(result, error_desc)

    # L3 fallback
    result = dict(l1_result)
    result["confidence"] = "low"
    result["tier"] = "L3"
    result["reasoning"] = f"L3 fallback after low L1 confidence ({confidence_value:.2f}) and failed or unavailable L2."
    return _ensure_keys(result, error_desc)
