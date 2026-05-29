"""Nezha Demon Hunt — single-head investigation tool.

L1 (Claude Code) orchestrates multi-head parallelism by calling this tool
multiple times with different head_type values.
"""
import json
from datetime import datetime, timezone

from skills.tool_bajiu.scripts.providers import get_available_provider


_PROMPTS = {
    "business": """You are Nezha's Business Head (妖魔头). Analyze the target from business logic perspective.

Target: {target}
Context: {context}
Mode: {mode}

Focus on:
- Requirement compliance
- Business boundary scenarios
- Exception flow handling
- Data validation points

Output ONLY a JSON object with this exact schema:
{{"findings": [{{"id": "B001", "severity": "high|medium|low", "description": "...", "scenario": "..."}}], "confidence": "high|medium|low"}}""",

    "code": """You are Nezha's Code Head (除魔头). Analyze the target from code logic perspective.

Target: {target}
Context: {context}
Mode: {mode}

Focus on:
- AST structure risks
- Dependency chain analysis
- Bug pattern matching
- Performance issues
- Security pattern checks

Output ONLY a JSON object with this exact schema:
{{"findings": [{{"id": "C001", "severity": "critical|high|medium|low", "category": "null_pointer|injection|...", "description": "...", "pattern": "..."}}], "confidence": "high|medium|low"}}""",

    "cognitive": """You are Nezha's Cognitive Head (灵珠头). Investigate the target comprehensively and identify root cause.

Target: {target}
Context: {context}
Mode: {mode}

Output ONLY a JSON object:
{{"root_causes": [{{"id": "RC001", "confidence": "high|medium|low", "description": "...", "evidence": "...", "surface_symptom": "...", "true_nature": "..."}}], "business_risks": [{{"id": "BR001", "severity": "high|medium|low", "description": "..."}}], "code_risks": [{{"id": "CR001", "severity": "critical|high|medium|low", "category": "...", "description": "..."}}], "suggested_fixes": [{{"id": "SF001", "priority": "P0|P1|P2", "description": "...", "files_affected": ["..."]}}]}}""",
}


def _call_ai(system_prompt: str, user_prompt: str) -> dict:
    """Call AI provider and parse JSON response."""
    provider = get_available_provider()
    if provider is None:
        return {}
    try:
        raw = provider.infer(system_prompt, user_prompt, timeout=10.0)
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except Exception:
        return {}


def demon_hunt(
    target: str,
    mode: str = "bug_hunt",
    head_type: str = "cognitive",
    context: str = "",
) -> str:
    """Execute single-head investigation.

    Args:
        target: Target file path, code snippet, or problem description.
        mode: "bug_hunt" | "code_review" | "suspicious_scan".
        head_type: "business" | "code" | "cognitive". L1 decides which to call.
        context: Optional context (requirements, history, other persona reports).

    Returns:
        Structured investigation output in [block_name]: value format.
    """
    prompt = _PROMPTS.get(head_type, _PROMPTS["cognitive"])
    result = _call_ai(
        prompt.format(target=target, context=context, mode=mode),
        f"Analyze from {head_type} perspective.",
    )

    if not result:
        result = {
            "findings": [{"id": "F-001", "description": "Fallback — no AI provider available"}],
            "root_causes": [{"id": "RC-001", "description": "Fallback — no AI provider available", "evidence": "N/A"}],
            "confidence": "low",
        }

    return _format_output(result, head_type)


def _format_output(data: dict, head_type: str) -> str:
    """Format output in [block_name]: value format per SPEC.md."""
    lines = [
        "[task_status]: completed",
        f'[output_summary]: {(data.get("findings") or [{}])[0].get("description", "Investigation complete") if head_type != "cognitive" else (data.get("root_causes") or [{}])[0].get("description", "Investigation complete")}',
        "[capability_used]: problem_solving",
        f'[tags]: debug, {head_type}',
        "",
        f"[demon_hunt_result]: head_type={head_type}",
    ]

    if head_type == "cognitive":
        lines.append("")
        lines.append("[root_cause]:")
        for rc in data.get("root_causes", []):
            lines.append(f"  - id: {rc.get('id', 'RC-001')}")
            lines.append(f'    confidence: {rc.get("confidence", "medium")}')
            lines.append(f'    description: "{rc.get("description", "")}"')
            lines.append(f'    evidence: "{rc.get("evidence", "N/A")}"')
            lines.append(f'    surface_symptom: "{rc.get("surface_symptom", "")}"')
            lines.append(f'    true_nature: "{rc.get("true_nature", "")}"')

        lines.append("")
        lines.append("[business_risk]:")
        for br in data.get("business_risks", []):
            lines.append(f"  - id: {br.get('id', 'BR-001')}")
            lines.append(f'    severity: {br.get("severity", "medium")}')
            lines.append(f'    description: "{br.get("description", "")}"')

        lines.append("")
        lines.append("[code_risk]:")
        for cr in data.get("code_risks", []):
            lines.append(f"  - id: {cr.get('id', 'CR-001')}")
            lines.append(f'    severity: {cr.get("severity", "medium")}')
            lines.append(f'    category: {cr.get("category", "logic_error")}')
            lines.append(f'    description: "{cr.get("description", "")}"')

        lines.append("")
        lines.append("[suggested_fixes]:")
        for sf in data.get("suggested_fixes", []):
            lines.append(f"  - id: {sf.get('id', 'SF-001')}")
            lines.append(f'    priority: {sf.get("priority", "P1")}')
            lines.append(f'    description: "{sf.get("description", "")}"')
            files = sf.get("files_affected", [])
            lines.append(f'    files_affected: {files}')
    else:
        lines.append("")
        lines.append("[findings]:")
        for f in data.get("findings", []):
            lines.append(f"  - id: {f.get('id', 'F-001')}")
            lines.append(f'    severity: {f.get("severity", "medium")}')
            lines.append(f'    description: "{f.get("description", "")}"')
            if "scenario" in f:
                lines.append(f'    scenario: "{f["scenario"]}"')
            if "category" in f:
                lines.append(f'    category: {f["category"]}"')
            if "pattern" in f:
                lines.append(f'    pattern: "{f["pattern"]}"')

    lines.append("")
    lines.append("[next_action]: Synthesize findings. If business/code perspective is missing, call demon_hunt with corresponding head_type.")
    lines.append("[persona_handoff]:")
    lines.append('  recommended_executor: "execution-capable-persona"')
    lines.append(f'  context_summary: "{(data.get("findings") or [{}])[0].get("description", "Investigation complete") if head_type != "cognitive" else (data.get("root_causes") or [{}])[0].get("description", "Investigation complete")}"')

    return "\n".join(lines)
