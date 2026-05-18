"""Task difficulty assessment and skill routing."""
from typing import List


def analyze_task(task_context: str, skill_profiles: List[dict]) -> dict:
    """
    Assess task difficulty and match candidate skills.

    Args:
        task_context: Task description or handoff report
        skill_profiles: List of {name, description, tools} from skill scanner

    Returns:
        {difficulty, matched_candidates, factors}
    """
    factors = _extract_factors(task_context)
    candidates = []

    # Check each candidate against prerequisites
    for profile in skill_profiles:
        name = profile.get("name", "")
        prereq = _check_prerequisites(name, task_context, factors)
        if prereq["passed"]:
            affinity = _calculate_affinity(name, factors)
            candidates.append({
                "name": name,
                "reason": prereq["reason"],
                "score": round(affinity, 2),
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Determine difficulty from best match
    if not candidates:
        difficulty = "UNDETERMINED"
    elif "yindan" in candidates[0]["name"]:
        difficulty = "TRIVIAL"
    elif "taie" in candidates[0]["name"]:
        difficulty = "MODERATE"
    elif "sanjian" in candidates[0]["name"]:
        difficulty = "COMPLEX"
    elif "kaishan" in candidates[0]["name"]:
        difficulty = "CRITICAL"
    else:
        difficulty = "MODERATE"

    return {
        "difficulty": difficulty,
        "matched_candidates": candidates,
        "factors": factors,
    }


def route_task(task_context: str, difficulty: str, matched_candidates: List[dict]) -> dict:
    """
    Generate execution plan based on analysis results.

    Returns:
        {execution_plan, routing_summary}
    """
    # Check for explicit skill recommendation in handoff report
    recommended = None
    if "[recommended_skill]:" in task_context:
        for line in task_context.split("\n"):
            if "[recommended_skill]:" in line:
                recommended = line.split(":")[-1].strip()
                break

    plan = []
    if recommended:
        plan.append({"step": 1, "skill": recommended, "action": f"Execute as recommended by investigation"})
    elif matched_candidates:
        best = matched_candidates[0]
        plan.append({"step": 1, "skill": best["name"], "action": f"Matched with score {best['score']}: {best['reason']}"})
    else:
        plan.append({"step": 1, "skill": "none", "action": "No skill matched. Suggest further investigation."})

    return {
        "execution_plan": plan,
        "routing_summary": f"Difficulty: {difficulty}, routed to: {plan[0]['skill']}",
    }


def _extract_factors(ctx: str) -> dict:
    """Extract decision factors from task context."""
    ctx_lower = ctx.lower() if ctx else ""

    is_fix = any(k in ctx_lower for k in ["fix", "repair", "patch", "修复", "修正", "替换"])
    is_create = any(k in ctx_lower for k in ["add", "create", "implement", "feature", "新增", "创建", "开发"])
    is_rewrite = any(k in ctx_lower for k in ["refactor", "rewrite", "restructure", "重构", "重写", "重组"])
    is_delete = any(k in ctx_lower for k in ["delete", "remove", "cleanup", "deprecated", "删除", "清理", "废弃"])

    scope = 0.3
    if any(k in ctx_lower for k in ["multi-file", "multiple files", "cross-module", "global", "entire", "all files", "多文件", "跨模块", "全局", "整个"]):
        scope = 1.0
    elif any(k in ctx_lower for k in ["several", "a few files", "related", "几个文件", "关联"]):
        scope = 0.6
    elif any(k in ctx_lower for k in ["single", "this file", "one file", "单文件", "局部", "这个文件"]):
        scope = 0.1

    return {
        "is_fix": is_fix,
        "is_create": is_create,
        "is_rewrite": is_rewrite,
        "is_delete": is_delete,
        "scope": scope,
    }


def _check_prerequisites(skill_name: str, ctx: str, factors: dict) -> dict:
    """Check if a skill's prerequisites are met."""
    if "yindan" in skill_name:
        if factors["is_fix"] and factors["scope"] <= 0.3:
            return {"passed": True, "reason": "Small-scope fix"}
        return {"passed": False, "reason": "Not a small-scope fix"}

    if "taie" in skill_name:
        if factors["is_create"] and not factors["is_rewrite"]:
            return {"passed": True, "reason": "Feature development"}
        if factors["is_fix"] and factors["scope"] > 0.3:
            return {"passed": True, "reason": "Larger-scope modification"}
        return {"passed": False, "reason": "Not feature development"}

    if "sanjian" in skill_name:
        if factors["is_rewrite"] and factors["scope"] >= 0.4:
            return {"passed": True, "reason": "Multi-file refactoring"}
        return {"passed": False, "reason": "Not multi-file refactoring"}

    if "kaishan" in skill_name:
        if factors["is_delete"] and factors["scope"] >= 0.4:
            return {"passed": True, "reason": "Bulk deletion/cleanup"}
        return {"passed": False, "reason": "Not bulk deletion"}

    return {"passed": False, "reason": "Unknown skill"}


def _calculate_affinity(skill_name: str, factors: dict) -> float:
    """Calculate affinity score for a skill."""
    if "yindan" in skill_name:
        return 0.8 if factors["is_fix"] else 0.3
    if "taie" in skill_name:
        return 0.8 if factors["is_create"] else 0.4
    if "sanjian" in skill_name:
        return 0.7 + factors["scope"] * 0.2 if factors["is_rewrite"] else 0.3
    if "kaishan" in skill_name:
        return 0.8 if factors["is_delete"] else 0.2
    return 0.3
