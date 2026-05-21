"""Nezha Demon Hunt — parallel investigation with Three Heads."""
import json
from datetime import datetime, timezone

from skills.tool_bajiu.scripts.providers import get_available_provider
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode


_BUSINESS_PROMPT = """You are Nezha's Business Head (妖魔头). Analyze the target from business logic perspective.

Target: {target}
Context: {context}
Mode: {mode}

Focus on:
- Requirement compliance
- Business boundary scenarios
- Exception flow handling
- Data validation points

Output ONLY a JSON object with this exact schema:
{{"findings": [{{"id": "B001", "severity": "high|medium|low", "description": "...", "scenario": "..."}}], "confidence": "high|medium|low"}}"""

_CODE_PROMPT = """You are Nezha's Code Head (除魔头). Analyze the target from code logic perspective.

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
{{"findings": [{{"id": "C001", "severity": "critical|high|medium|low", "category": "null_pointer|injection|...", "description": "...", "pattern": "..."}}], "confidence": "high|medium|low"}}"""

_COGNITIVE_PROMPT = """You are Nezha's Cognitive Head (灵珠头). Synthesize findings and identify root cause.

Target: {target}
Business Findings: {business_findings}
Code Findings: {code_findings}

Output ONLY a JSON object:
{{"root_causes": [{{"id": "RC001", "confidence": "high|medium|low", "description": "...", "evidence": "...", "surface_symptom": "...", "true_nature": "..."}}], "suggested_fixes": [{{"id": "SF001", "priority": "P0|P1|P2", "description": "...", "files_affected": ["..."]}}]}}"""

_SINGLE_HEAD_PROMPT = """You are Nezha. Investigate the following target comprehensively.

Target: {target}
Context: {context}
Mode: {mode}

Output a structured investigation report with:
- root_cause: The definitive reason for the issue
- business_risks: Any business logic concerns
- code_risks: Any code-level issues
- suggested_fixes: Prioritized fix recommendations

Output ONLY a JSON object with these keys: root_causes, business_risks, code_risks, suggested_fixes."""


def _call_ai(system_prompt: str, user_prompt: str) -> dict:
    """Call AI provider and parse JSON response."""
    provider = get_available_provider()
    if provider is None:
        return {}
    try:
        raw = provider.infer(system_prompt, user_prompt, timeout=10.0)
        # Extract JSON if wrapped in markdown
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
    context: str = "",
    file_count: int = 1,
    line_change_est: int = 0,
    complexity: str = "simple",
    risk_level: str = "low",
) -> str:
    """Execute demon hunt investigation.

    Args:
        target: Target file path, code snippet, or problem description.
        mode: "bug_hunt" | "code_review" | "suspicious_scan".
        context: Optional context (requirements, history, other agent reports).
        file_count: Number of files involved (for workload assessment).
        line_change_est: Estimated lines of change.
        complexity: "simple" | "moderate" | "complex".
        risk_level: "low" | "medium" | "high" | "critical".

    Returns:
        Structured investigation report string.
    """
    execution_mode = assess_workload(file_count, line_change_est, complexity, risk_level)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if execution_mode == ExecutionMode.SINGLE_HEAD:
        return _investigate_single_head(target, mode, context, timestamp)
    elif execution_mode == ExecutionMode.DUAL_HEAD:
        return _investigate_dual_head(target, mode, context, timestamp)
    else:
        return _investigate_trinity(target, mode, context, timestamp)


def _investigate_single_head(target: str, mode: str, context: str, timestamp: str) -> str:
    """Single head investigation (cognitive only)."""
    prompt = _SINGLE_HEAD_PROMPT.format(target=target, context=context, mode=mode)
    result = _call_ai(prompt, "Please investigate and return structured JSON.")

    if not result:
        result = {
            "root_causes": [{"id": "RC-001", "description": "Fallback analysis — no AI provider available", "evidence": "N/A"}],
            "business_risks": [],
            "code_risks": [],
            "suggested_fixes": [],
        }

    return _format_report(result, target, mode, timestamp, "single_head")


def _investigate_dual_head(target: str, mode: str, context: str, timestamp: str) -> str:
    """Dual head investigation (cognitive + auxiliary)."""
    if mode == "code_review":
        aux_prompt = _BUSINESS_PROMPT
        aux_label = "business"
    else:
        aux_prompt = _CODE_PROMPT
        aux_label = "code"

    aux_result = _call_ai(
        aux_prompt.format(target=target, context=context, mode=mode),
        f"Analyze from {aux_label} perspective.",
    )
    cognitive_result = _call_ai(
        _COGNITIVE_PROMPT.format(
            target=target,
            business_findings=json.dumps(aux_result.get("findings", [])) if aux_label == "business" else "[]",
            code_findings=json.dumps(aux_result.get("findings", [])) if aux_label == "code" else "[]",
        ),
        "Synthesize and identify root cause.",
    )

    combined = {
        "root_causes": cognitive_result.get("root_causes", []),
        "business_risks": aux_result.get("findings", []) if aux_label == "business" else [],
        "code_risks": aux_result.get("findings", []) if aux_label == "code" else [],
        "suggested_fixes": cognitive_result.get("suggested_fixes", []),
    }

    return _format_report(combined, target, mode, timestamp, "dual_head")


def _investigate_trinity(target: str, mode: str, context: str, timestamp: str) -> str:
    """Trinity investigation — placeholder for Task 4."""
    return _investigate_single_head(target, mode, context, timestamp)


def _format_report(data: dict, target: str, mode: str, timestamp: str, execution_mode: str) -> str:
    """Format investigation data into structured report."""
    lines = [
        "[nezha_report]:",
        f'  timestamp: "{timestamp}"',
        f'  target: "{target}"',
        f'  mode: "{mode}"',
        f'  execution_mode: "{execution_mode}"',
        "",
        "[root_cause]:",
    ]
    for rc in data.get("root_causes", []):
        lines.append(f"  - id: {rc.get('id', 'RC-001')}")
        lines.append(f'    confidence: {rc.get("confidence", "medium")}')
        lines.append(f'    description: "{rc.get("description", "Unknown")}"')
        lines.append(f'    evidence: "{rc.get("evidence", "N/A")}"')

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

    lines.append("")
    lines.append("[agent_handoff]:")
    lines.append('  recommended_executor: "execution-capable-agent"')
    lines.append(f'  context_summary: "{data.get("root_causes", [{}])[0].get("description", "Investigation complete")}"')
    lines.append(f'  report_ref: "nezha-{timestamp}"')

    return "\n".join(lines)
