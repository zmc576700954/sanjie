# Nezha Three Heads Six Arms Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `nezha_demon_hunt` (investigation) and `nezha_lotus_body` (execution) skills with Three Heads Six Arms parallel capabilities, workload assessment, and pre-execution assignment planning.

**Architecture:** Two core Python modules (`demon_hunt.py` for parallel investigation, `lotus_body.py` for parallel execution) plus supporting modules (`workload_assessor.py`, `assignment_planner.py`). All modules use the existing `tool_bajiu` provider system for AI inference. Three modes: `single_head` (simple), `dual_head` (moderate), `trinity_six_arms` (complex). Pre-execution assignment happens before any parallel work to prevent conflicts.

**Tech Stack:** Python 3.10+, pytest, concurrent.futures (for parallel AI calls), existing `tool_bajiu` provider system, existing `a2a_utils` for agent handoff.

---

## File Structure

| File | Responsibility |
|------|---------------|
| `skills/tool_nezha/scripts/workload_assessor.py` | Evaluates workload and selects execution mode (single_head / dual_head / trinity_six_arms) |
| `skills/tool_nezha/scripts/assignment_planner.py` | Generates pre-execution assignment plans for trinity mode, defining head/arm boundaries |
| `skills/tool_nezha/scripts/demon_hunt.py` | Implements `nezha_demon_hunt` — parallel investigation with three heads, outputs structured report |
| `skills/tool_nezha/scripts/lotus_body.py` | Implements `nezha_lotus_body` — parallel execution with six arms, outputs execution results |
| `skills/tool_nezha/SKILL.md` | Skill manifest registering all tools with YAML frontmatter |
| `agents/nezha.md` | Updated agent persona with Three Heads Six Arms capabilities |
| `tests/test_workload_assessor.py` | Unit tests for workload assessment |
| `tests/test_assignment_planner.py` | Unit tests for assignment planning |
| `tests/test_demon_hunt.py` | Unit tests for demon hunt (all three modes) |
| `tests/test_lotus_body.py` | Unit tests for lotus body (all three modes) |

---

### Task 1: Workload Assessment Module

**Files:**
- Create: `skills/tool_nezha/scripts/__init__.py`
- Create: `skills/tool_nezha/scripts/workload_assessor.py`
- Test: `tests/test_workload_assessor.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p skills/tool_nezha/scripts
touch skills/tool_nezha/scripts/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_workload_assessor.py`:

```python
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode


class TestWorkloadAssessor:
    def test_single_head_simple(self):
        result = assess_workload(
            file_count=1,
            line_change_est=30,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.SINGLE_HEAD

    def test_single_head_boundary(self):
        result = assess_workload(
            file_count=2,
            line_change_est=50,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.SINGLE_HEAD

    def test_dual_head_moderate(self):
        result = assess_workload(
            file_count=3,
            line_change_est=100,
            complexity="moderate",
            risk_level="medium",
        )
        assert result == ExecutionMode.DUAL_HEAD

    def test_trinity_high_file_count(self):
        result = assess_workload(
            file_count=6,
            line_change_est=100,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS

    def test_trinity_high_lines(self):
        result = assess_workload(
            file_count=2,
            line_change_est=250,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS

    def test_trinity_complex(self):
        result = assess_workload(
            file_count=2,
            line_change_est=50,
            complexity="complex",
            risk_level="low",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS

    def test_trinity_critical_risk(self):
        result = assess_workload(
            file_count=1,
            line_change_est=30,
            complexity="simple",
            risk_level="critical",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_workload_assessor.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skills.tool_nezha.scripts.workload_assessor'`

- [ ] **Step 4: Write minimal implementation**

Create `skills/tool_nezha/scripts/workload_assessor.py`:

```python
"""Workload assessment for Nezha's Three Heads Six Arms mode selection."""
from enum import Enum


class ExecutionMode(str, Enum):
    SINGLE_HEAD = "single_head"
    DUAL_HEAD = "dual_head"
    TRINITY_SIX_ARMS = "trinity_six_arms"


def assess_workload(
    file_count: int,
    line_change_est: int,
    complexity: str,
    risk_level: str,
) -> ExecutionMode:
    """Assess workload and select execution mode.

    Args:
        file_count: Number of files involved.
        line_change_est: Estimated lines of change.
        complexity: "simple" | "moderate" | "complex".
        risk_level: "low" | "medium" | "high" | "critical".

    Returns:
        ExecutionMode: SINGLE_HEAD, DUAL_HEAD, or TRINITY_SIX_ARMS.
    """
    # Trinity triggers on any high-complexity indicator
    if (
        file_count > 5
        or line_change_est > 200
        or complexity == "complex"
        or risk_level == "critical"
    ):
        return ExecutionMode.TRINITY_SIX_ARMS

    # Dual head for moderate workloads
    if (
        file_count <= 5
        and line_change_est <= 200
        and complexity == "moderate"
    ):
        return ExecutionMode.DUAL_HEAD

    # Default to single head for simple workloads
    return ExecutionMode.SINGLE_HEAD
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_workload_assessor.py -v`

Expected: All 7 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/tool_nezha/scripts/__init__.py skills/tool_nezha/scripts/workload_assessor.py tests/test_workload_assessor.py
git commit -m "feat(nezha): add workload assessment module

- ExecutionMode enum with single_head / dual_head / trinity_six_arms
- assess_workload() with file_count, line_change_est, complexity, risk_level criteria
- Full test coverage for all mode selection paths

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Assignment Planner Module

**Files:**
- Create: `skills/tool_nezha/scripts/assignment_planner.py`
- Test: `tests/test_assignment_planner.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_assignment_planner.py`:

```python
from skills.tool_nezha.scripts.assignment_planner import (
    create_assignment_plan,
    HeadRole,
    ArmAssignment,
)


class TestAssignmentPlanner:
    def test_single_head_plan(self):
        plan = create_assignment_plan(
            mode="single_head",
            target_files=["core.py"],
            task_description="Fix null pointer",
        )
        assert plan["mode"] == "single_head"
        assert "head_assignments" not in plan or plan.get("head_assignments") is None
        assert "arm_assignments" not in plan or plan.get("arm_assignments") is None

    def test_dual_head_plan(self):
        plan = create_assignment_plan(
            mode="dual_head",
            target_files=["core.py", "utils.py"],
            task_description="Refactor payment logic",
            auxiliary_head="code_head",
        )
        assert plan["mode"] == "dual_head"
        assert len(plan["head_assignments"]) == 2
        assert "cognitive_head" in plan["head_assignments"]
        assert "code_head" in plan["head_assignments"]

    def test_trinity_head_assignments(self):
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=["core/service.py", "core/model.py", "handlers/edge.py"],
            task_description="Major refactoring",
        )
        assert plan["mode"] == "trinity_six_arms"
        heads = plan["head_assignments"]
        assert len(heads) == 3
        assert "cognitive_head" in heads
        assert "business_head" in heads
        assert "code_head" in heads
        assert heads["cognitive_head"]["role"] == HeadRole.CONTEXT_MASTER.value
        assert heads["business_head"]["role"] == HeadRole.BUSINESS_ANALYZER.value
        assert heads["code_head"]["role"] == HeadRole.CODE_ANALYZER.value

    def test_trinity_arm_assignments(self):
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=["core/service.py", "handlers/edge.py", "utils/helpers.py"],
            task_description="Major refactoring",
        )
        arms = plan["arm_assignments"]
        assert len(arms) == 3
        assert "main_arms" in arms
        assert "left_arms" in arms
        assert "right_arms" in arms
        assert arms["main_arms"]["head"] == "cognitive_head"
        assert arms["left_arms"]["head"] == "business_head"
        assert arms["right_arms"]["head"] == "code_head"
        # Verify execution order
        assert plan["execution_order"][0]["arms"] == ["main_arms"]
        assert plan["execution_order"][1]["arms"] == ["left_arms", "right_arms"]

    def test_arm_scope_no_overlap(self):
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=["a.py", "b.py", "c.py"],
            task_description="Test",
        )
        arms = plan["arm_assignments"]
        all_files = []
        for arm_name, arm_data in arms.items():
            all_files.extend(arm_data["files"])
        # Each file assigned to exactly one arm
        assert len(all_files) == len(set(all_files))
        assert set(all_files) == {"a.py", "b.py", "c.py"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_assignment_planner.py -v`

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

Create `skills/tool_nezha/scripts/assignment_planner.py`:

```python
"""Pre-execution assignment planner for Nezha's Three Heads Six Arms."""
from enum import Enum
from typing import Optional


class HeadRole(str, Enum):
    CONTEXT_MASTER = "context_master"
    BUSINESS_ANALYZER = "business_analyzer"
    CODE_ANALYZER = "code_analyzer"


def create_assignment_plan(
    mode: str,
    target_files: list[str],
    task_description: str,
    auxiliary_head: Optional[str] = None,
) -> dict:
    """Create a pre-execution assignment plan.

    Args:
        mode: "single_head" | "dual_head" | "trinity_six_arms".
        target_files: List of files involved.
        task_description: Description of the task.
        auxiliary_head: For dual_head mode, which auxiliary head to use ("business_head" or "code_head").

    Returns:
        Assignment plan dict.
    """
    plan = {
        "mode": mode,
        "assessment_reason": task_description,
    }

    if mode == "single_head":
        return plan

    if mode == "dual_head":
        aux = auxiliary_head or "code_head"
        plan["head_assignments"] = {
            "cognitive_head": {
                "role": HeadRole.CONTEXT_MASTER.value,
                "tasks": ["Parse context", "Identify logic paths", "Final synthesis"],
                "deliverable": "[synthesis]",
            },
            aux: {
                "role": HeadRole.CODE_ANALYZER.value if aux == "code_head" else HeadRole.BUSINESS_ANALYZER.value,
                "tasks": ["Analyze target domain"],
                "deliverable": "[analysis]",
            },
        }
        return plan

    if mode == "trinity_six_arms":
        # Distribute files across three arms without overlap
        file_count = len(target_files)
        main_count = max(1, file_count // 3 + (1 if file_count % 3 > 0 else 0))
        left_count = max(1, file_count // 3 + (1 if file_count % 3 > 1 else 0))

        main_files = target_files[:main_count]
        left_files = target_files[main_count:main_count + left_count]
        right_files = target_files[main_count + left_count:]
        if not right_files:
            right_files = [left_files.pop()] if len(left_files) > 1 else main_files[:1]

        plan["head_assignments"] = {
            "cognitive_head": {
                "role": HeadRole.CONTEXT_MASTER.value,
                "tasks": [
                    "Parse global business context",
                    "Identify core vs secondary logic paths",
                    "Final root cause confirmation and priority sorting",
                ],
                "deliverable": "[synthesis] + [priority_matrix]",
            },
            "business_head": {
                "role": HeadRole.BUSINESS_ANALYZER.value,
                "tasks": [
                    "Map business rules and boundary conditions",
                    "Verify requirement compliance",
                    "Identify exception flows and missing data validation",
                ],
                "deliverable": "[business_risk] + [boundary_scenarios]",
            },
            "code_head": {
                "role": HeadRole.CODE_ANALYZER.value,
                "tasks": [
                    "AST structure analysis",
                    "Dependency chain tracing",
                    "Bug pattern matching and security scanning",
                ],
                "deliverable": "[code_risk] + [dependency_map]",
            },
        }

        plan["arm_assignments"] = {
            "main_arms": {
                "head": "cognitive_head",
                "scope": "Core logic files",
                "files": main_files,
                "task_type": "critical_fix",
                "description": "Fix root cause in core business logic",
                "dependencies": [],
            },
            "left_arms": {
                "head": "business_head",
                "scope": "Secondary business logic + boundary handling",
                "files": left_files,
                "task_type": "boundary_handling",
                "description": "Add boundary conditions, adjust defaults, improve exception handling",
                "dependencies": ["main_arms"],
            },
            "right_arms": {
                "head": "code_head",
                "scope": "Code structure optimization",
                "files": right_files,
                "task_type": "structural_optimize",
                "description": "Optimize imports, fix type hints, supplement unit tests",
                "dependencies": ["main_arms"],
            },
        }

        plan["execution_order"] = [
            {"phase": 1, "arms": ["main_arms"], "parallel": False},
            {"phase": 2, "arms": ["left_arms", "right_arms"], "parallel": True},
        ]

        plan["conflict_prevention"] = [
            "All arms' files are declared before execution, no overlapping regions",
            "If cross-file dependencies exist, auto-serialize",
            "Execution order: main_arms -> left_arms + right_arms (parallel)",
        ]

    return plan
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_assignment_planner.py -v`

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/tool_nezha/scripts/assignment_planner.py tests/test_assignment_planner.py
git commit -m "feat(nezha): add assignment planner module

- create_assignment_plan() supports single_head / dual_head / trinity_six_arms
- Trinity mode distributes files across main/left/right arms without overlap
- Defines execution order: main_arms first, then left+right in parallel
- HeadRole enum for cognitive/business/code analyzer roles

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Demon Hunt Core — Single Head & Dual Head Modes

**Files:**
- Create: `skills/tool_nezha/scripts/demon_hunt.py`
- Test: `tests/test_demon_hunt.py`

- [ ] **Step 1: Write the failing test (single head + dual head)**

Create `tests/test_demon_hunt.py`:

```python
from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.demon_hunt import demon_hunt


class TestDemonHuntSingleHead:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_single_head_returns_report(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"findings": [{"id": "F1", "description": "Null check missing"}], '
            '"confidence": "high", "evidence": "line 42"}'
        )
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            file_count=1,
            line_change_est=20,
            complexity="simple",
            risk_level="low",
        )

        assert "[nezha_report]" in result
        assert "single_head" in result
        assert "[root_cause]" in result
        mock_provider.infer.assert_called_once()

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_single_head_no_provider_fallback(self, mock_get_provider):
        mock_get_provider.return_value = None

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            file_count=1,
            line_change_est=20,
            complexity="simple",
            risk_level="low",
        )

        assert "[nezha_report]" in result
        assert "[root_cause]" in result
        assert "Fallback analysis" in result


class TestDemonHuntDualHead:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_dual_head_calls_twice(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.side_effect = [
            '{"findings": [{"id": "F1", "description": "Business rule violation"}], "confidence": "high", "evidence": "req doc"}',
            '{"findings": [{"id": "F2", "description": "Null pointer risk"}], "confidence": "high", "evidence": "line 42"}',
        ]
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="payment.py",
            mode="code_review",
            file_count=3,
            line_change_est=100,
            complexity="moderate",
            risk_level="medium",
        )

        assert "[nezha_report]" in result
        assert "dual_head" in result
        assert "[business_risk]" in result
        assert "[code_risk]" in result
        assert mock_provider.infer.call_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_demon_hunt.py::TestDemonHuntSingleHead -v`

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation (single head + dual head)**

Create `skills/tool_nezha/scripts/demon_hunt.py`:

```python
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

    # Mode-specific investigation
    if execution_mode == ExecutionMode.SINGLE_HEAD:
        return _investigate_single_head(target, mode, context, timestamp)
    elif execution_mode == ExecutionMode.DUAL_HEAD:
        return _investigate_dual_head(target, mode, context, timestamp)
    else:
        # Trinity mode — handled in next task
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
    """Dual head investigation (cognitive + code head for bug_hunt, cognitive + business for code_review)."""
    # Choose auxiliary head based on mode
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_demon_hunt.py::TestDemonHuntSingleHead tests/test_demon_hunt.py::TestDemonHuntDualHead -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/tool_nezha/scripts/demon_hunt.py tests/test_demon_hunt.py
git commit -m "feat(nezha): add demon_hunt core with single_head and dual_head modes

- demon_hunt() with workload assessment integration
- Single head: direct cognitive investigation
- Dual head: cognitive + auxiliary head (business or code based on mode)
- AI provider integration via tool_bajiu provider system
- Fallback when no AI provider available
- Structured report output with nezha_report, root_cause, business_risk, code_risk, suggested_fixes

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Demon Hunt Core — Trinity Six Arms Mode

**Files:**
- Modify: `skills/tool_nezha/scripts/demon_hunt.py`
- Modify: `tests/test_demon_hunt.py`

- [ ] **Step 1: Write the failing test (trinity mode)**

Add to `tests/test_demon_hunt.py`:

```python
import json


class TestDemonHuntTrinity:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_trinity_calls_three_times(self, mock_get_provider):
        mock_provider = MagicMock()
        # 3 calls: business head, code head, cognitive head (synthesis)
        mock_provider.infer.side_effect = [
            '{"findings": [{"id": "B001", "severity": "high", "description": "Business rule violation", "scenario": "edge case"}]}',
            '{"findings": [{"id": "C001", "severity": "critical", "category": "null_pointer", "description": "Null risk", "pattern": "missing check"}]}',
            '{"root_causes": [{"id": "RC001", "confidence": "high", "description": "Root cause found", "evidence": "line 42", "surface_symptom": "crash", "true_nature": "missing validation"}], "suggested_fixes": [{"id": "SF001", "priority": "P0", "description": "Add validation", "files_affected": ["core.py"]}]}',
        ]
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="high",
        )

        assert "[nezha_report]" in result
        assert "trinity_six_arms" in result
        assert "[business_risk]" in result
        assert "[code_risk]" in result
        assert "[root_cause]" in result
        assert "Business rule violation" in result
        assert "Null risk" in result
        assert "Root cause found" in result
        assert mock_provider.infer.call_count == 3

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_trinity_with_context(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.side_effect = [
            '{"findings": []}',
            '{"findings": []}',
            '{"root_causes": [{"id": "RC001", "confidence": "medium", "description": "Context-driven root cause", "evidence": "YangJian report"}], "suggested_fixes": []}',
        ]
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="service.py",
            mode="bug_hunt",
            context="YangJian report: possible race condition",
            file_count=6,
            line_change_est=300,
            complexity="complex",
            risk_level="critical",
        )

        assert "trinity_six_arms" in result
        assert "Context-driven root cause" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_demon_hunt.py::TestDemonHuntTrinity -v`

Expected: FAIL — trinity mode currently falls back to single_head, so `trinity_six_arms` not in output.

- [ ] **Step 3: Implement trinity mode in demon_hunt.py**

Replace the `_investigate_trinity` function in `skills/tool_nezha/scripts/demon_hunt.py`:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def _investigate_trinity(target: str, mode: str, context: str, timestamp: str) -> str:
    """Trinity investigation — three heads in parallel."""
    # Launch business head and code head in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        business_future = executor.submit(
            _call_ai,
            _BUSINESS_PROMPT.format(target=target, context=context, mode=mode),
            "Analyze from business perspective.",
        )
        code_future = executor.submit(
            _call_ai,
            _CODE_PROMPT.format(target=target, context=context, mode=mode),
            "Analyze from code perspective.",
        )

        business_result = business_future.result()
        code_result = code_future.result()

    # Cognitive head synthesizes both results
    cognitive_result = _call_ai(
        _COGNITIVE_PROMPT.format(
            target=target,
            business_findings=json.dumps(business_result.get("findings", [])),
            code_findings=json.dumps(code_result.get("findings", [])),
        ),
        "Synthesize findings and identify root cause.",
    )

    combined = {
        "root_causes": cognitive_result.get("root_causes", []),
        "business_risks": business_result.get("findings", []),
        "code_risks": code_result.get("findings", []),
        "suggested_fixes": cognitive_result.get("suggested_fixes", []),
    }

    return _format_report(combined, target, mode, timestamp, "trinity_six_arms")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_demon_hunt.py -v`

Expected: All tests PASS (single_head + dual_head + trinity).

- [ ] **Step 5: Commit**

```bash
git add skills/tool_nezha/scripts/demon_hunt.py tests/test_demon_hunt.py
git commit -m "feat(nezha): add trinity_six_arms mode to demon_hunt

- Three heads parallel investigation using ThreadPoolExecutor
- Business head + Code head run in parallel
- Cognitive head synthesizes results sequentially after both complete
- Trinity mode outputs full report with business_risk + code_risk + root_cause

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: Lotus Body Core — Single Arms Mode

**Files:**
- Create: `skills/tool_nezha/scripts/lotus_body.py`
- Test: `tests/test_lotus_body.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_lotus_body.py`:

```python
from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.lotus_body import lotus_body


class TestLotusBodySingleArms:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_single_arms_direct_instruction(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"execution_plan": [{"id": "EP-001", "priority": "P0", "target_file": "core.py", '
            '"line_range": "42-56", "change_type": "fix", "description": "Add null check"}], '
            '"execution_result": [{"id": "EP-001", "status": "success", "diff_summary": "Added null check", "files_modified": ["core.py"]}]}'
        )
        mock_get_provider.return_value = mock_provider

        result = lotus_body(
            input_source="direct_instruction",
            input_payload={"instruction": "Add null check to getBucket()"},
            file_count=1,
            line_change_est=10,
            complexity="simple",
            risk_level="low",
        )

        assert "[lotus_report]" in result
        assert "single_head" in result
        assert "[execution_plan]" in result
        assert "[execution_result]" in result
        mock_provider.infer.assert_called_once()

    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_single_arms_no_provider_fallback(self, mock_get_provider):
        mock_get_provider.return_value = None

        result = lotus_body(
            input_source="direct_instruction",
            input_payload={"instruction": "Fix typo"},
            file_count=1,
            line_change_est=5,
            complexity="simple",
            risk_level="low",
        )

        assert "[lotus_report]" in result
        assert "[execution_plan]" in result
        assert "Fallback execution" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lotus_body.py::TestLotusBodySingleArms -v`

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation (single arms)**

Create `skills/tool_nezha/scripts/lotus_body.py`:

```python
"""Nezha Lotus Body — parallel execution with Six Arms."""
import json
from datetime import datetime, timezone

from skills.tool_bajiu.scripts.providers import get_available_provider
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode


_SINGLE_ARMS_PROMPT = """You are Nezha. Execute the following modification task precisely.

Task: {task}
Scope Limit: {scope_limit}
Safety Level: {safety_level}

Output a JSON object with:
- execution_plan: list of tasks with id, priority, target_file, line_range, change_type, description
- execution_result: list of results with id, status, diff_summary, files_modified
- verification_checklist: list of verification items

Be surgical and precise. Do not over-engineer."""


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


def lotus_body(
    input_source: str,
    input_payload: dict,
    scope_limit: list = None,
    safety_level: str = "standard",
    file_count: int = 1,
    line_change_est: int = 0,
    complexity: str = "simple",
    risk_level: str = "low",
) -> str:
    """Execute lotus body refactoring.

    Args:
        input_source: "demon_hunt_report" | "direct_instruction" | "yangjian_handoff".
        input_payload: The report or instruction dict.
        scope_limit: Allowed file modification scope.
        safety_level: "strict" | "standard" | "aggressive".
        file_count: Number of files involved (for workload assessment).
        line_change_est: Estimated lines of change.
        complexity: "simple" | "moderate" | "complex".
        risk_level: "low" | "medium" | "high" | "critical".

    Returns:
        Structured execution report string.
    """
    execution_mode = assess_workload(file_count, line_change_est, complexity, risk_level)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    scope = scope_limit or []

    # Extract task description from payload
    if input_source == "demon_hunt_report":
        task = f"Execute fixes from report: {json.dumps(input_payload.get('suggested_fixes', []))}"
    elif input_source == "yangjian_handoff":
        task = f"Execute handoff: {input_payload.get('action', 'No action specified')}"
    else:
        task = input_payload.get("instruction", "No instruction provided")

    if execution_mode == ExecutionMode.SINGLE_HEAD:
        return _execute_single_arms(task, scope, safety_level, timestamp)
    elif execution_mode == ExecutionMode.DUAL_HEAD:
        return _execute_dual_arms(task, scope, safety_level, timestamp)
    else:
        # Trinity mode — handled in next task
        return _execute_single_arms(task, scope, safety_level, timestamp)


def _execute_single_arms(task: str, scope: list, safety_level: str, timestamp: str) -> str:
    """Single arms execution."""
    prompt = _SINGLE_ARMS_PROMPT.format(
        task=task,
        scope_limit=scope or ["all files"],
        safety_level=safety_level,
    )
    result = _call_ai(prompt, "Please generate execution plan and results.")

    if not result:
        result = {
            "execution_plan": [{"id": "EP-001", "priority": "P1", "description": "Fallback execution — no AI provider available"}],
            "execution_result": [{"id": "EP-001", "status": "partial", "diff_summary": "Unable to execute without AI provider"}],
            "verification_checklist": ["[ ] Verify changes manually"],
        }

    return _format_execution_report(result, timestamp, "single_head")


def _execute_dual_arms(task: str, scope: list, safety_level: str, timestamp: str) -> str:
    """Dual arms execution — placeholder, same as single for now."""
    return _execute_single_arms(task, scope, safety_level, timestamp)


def _format_execution_report(data: dict, timestamp: str, execution_mode: str) -> str:
    """Format execution data into structured report."""
    lines = [
        "[lotus_report]:",
        f'  timestamp: "{timestamp}"',
        f'  execution_mode: "{execution_mode}"',
        "",
        "[execution_plan]:",
    ]
    for ep in data.get("execution_plan", []):
        lines.append(f"  - id: {ep.get('id', 'EP-001')}")
        lines.append(f'    priority: {ep.get("priority", "P1")}')
        lines.append(f'    target_file: "{ep.get("target_file", "")}"')
        lines.append(f'    line_range: "{ep.get("line_range", "")}"')
        lines.append(f'    change_type: {ep.get("change_type", "fix")}')
        lines.append(f'    description: "{ep.get("description", "")}"')

    lines.append("")
    lines.append("[execution_result]:")
    for er in data.get("execution_result", []):
        lines.append(f"  - id: {er.get('id', 'EP-001')}")
        lines.append(f'    status: {er.get("status", "pending")}')
        lines.append(f'    diff_summary: "{er.get("diff_summary", "")}"')
        files = er.get("files_modified", [])
        lines.append(f'    files_modified: {files}')

    lines.append("")
    lines.append("[verification_checklist]:")
    for item in data.get("verification_checklist", []):
        lines.append(f"  - {item}")

    total = len(data.get("execution_plan", []))
    success = len([er for er in data.get("execution_result", []) if er.get("status") == "success"])
    lines.append("")
    lines.append(f"  total_changes: {total}")
    lines.append(f'  success_rate: "{success}/{total}"')
    lines.append('  next_steps: "Review changes and run tests."')

    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lotus_body.py::TestLotusBodySingleArms -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/tool_nezha/scripts/lotus_body.py tests/test_lotus_body.py
git commit -m "feat(nezha): add lotus_body core with single_arms mode

- lotus_body() with workload assessment integration
- Single arms: direct AI execution with execution_plan + execution_result + verification_checklist
- Supports input_source: demon_hunt_report, direct_instruction, yangjian_handoff
- Fallback when no AI provider available
- Structured execution report output

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: Lotus Body Core — Six Arms Mode

**Files:**
- Modify: `skills/tool_nezha/scripts/lotus_body.py`
- Modify: `tests/test_lotus_body.py`

- [ ] **Step 1: Write the failing test (six arms)**

Add to `tests/test_lotus_body.py`:

```python
class TestLotusBodySixArms:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_six_arms_trinity_mode(self, mock_get_provider):
        mock_provider = MagicMock()
        # 4 calls: assignment plan, main arms, left arms, right arms
        mock_provider.infer.side_effect = [
            # Assignment plan
            '{"arm_assignments": {"main_arms": {"files": ["core.py"], "task_type": "critical_fix"}, "left_arms": {"files": ["handlers.py"], "task_type": "boundary_handling"}, "right_arms": {"files": ["utils.py"], "task_type": "structural_optimize"}}, "execution_order": [{"phase": 1, "arms": ["main_arms"]}, {"phase": 2, "arms": ["left_arms", "right_arms"]}]}',
            # Main arms result
            '{"execution_plan": [{"id": "EP-M1", "priority": "P0", "target_file": "core.py", "change_type": "fix", "description": "Fix core logic"}], "execution_result": [{"id": "EP-M1", "status": "success", "diff_summary": "Fixed core", "files_modified": ["core.py"]}]}',
            # Left arms result
            '{"execution_plan": [{"id": "EP-L1", "priority": "P1", "target_file": "handlers.py", "change_type": "fix", "description": "Add boundary"}], "execution_result": [{"id": "EP-L1", "status": "success", "diff_summary": "Added boundary", "files_modified": ["handlers.py"]}]}',
            # Right arms result
            '{"execution_plan": [{"id": "EP-R1", "priority": "P2", "target_file": "utils.py", "change_type": "optimize", "description": "Optimize imports"}], "execution_result": [{"id": "EP-R1", "status": "success", "diff_summary": "Optimized", "files_modified": ["utils.py"]}]}',
        ]
        mock_get_provider.return_value = mock_provider

        result = lotus_body(
            input_source="direct_instruction",
            input_payload={"instruction": "Major refactoring across 8 files"},
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="high",
        )

        assert "[lotus_report]" in result
        assert "trinity_six_arms" in result
        assert "main_arms" in result
        assert "left_arms" in result
        assert "right_arms" in result
        assert "core.py" in result
        assert "handlers.py" in result
        assert "utils.py" in result
        assert mock_provider.infer.call_count == 4

    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_six_arms_with_demon_hunt_report(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.side_effect = [
            '{"arm_assignments": {"main_arms": {"files": ["a.py"]}, "left_arms": {"files": ["b.py"]}, "right_arms": {"files": ["c.py"]}}, "execution_order": [{"phase": 1, "arms": ["main_arms"]}, {"phase": 2, "arms": ["left_arms", "right_arms"]}]}',
            '{"execution_plan": [], "execution_result": []}',
            '{"execution_plan": [], "execution_result": []}',
            '{"execution_plan": [], "execution_result": []}',
        ]
        mock_get_provider.return_value = mock_provider

        report = {
            "suggested_fixes": [
                {"id": "SF-001", "priority": "P0", "files_affected": ["a.py"], "description": "Fix race condition"},
            ]
        }
        result = lotus_body(
            input_source="demon_hunt_report",
            input_payload=report,
            file_count=6,
            line_change_est=300,
            complexity="complex",
            risk_level="critical",
        )

        assert "trinity_six_arms" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lotus_body.py::TestLotusBodySixArms -v`

Expected: FAIL — trinity mode currently falls back to single_head.

- [ ] **Step 3: Implement six arms mode in lotus_body.py**

Replace `_execute_dual_arms` and add `_execute_six_arms` in `skills/tool_nezha/scripts/lotus_body.py`:

First, add the import at the top:

```python
from concurrent.futures import ThreadPoolExecutor
from skills.tool_nezha.scripts.assignment_planner import create_assignment_plan
```

Then replace the dual_arms placeholder and add six_arms:

```python
_MAIN_ARMS_PROMPT = """You are Nezha's Main Arms (灵珠头控制). Execute the core logic modification.

Task: {task}
Assigned Files: {files}
Scope Limit: {scope_limit}
Safety Level: {safety_level}

Output JSON with execution_plan and execution_result for your assigned files only."""

_LEFT_ARMS_PROMPT = """You are Nezha's Left Arms (妖魔头控制). Execute secondary business logic and boundary handling.

Task: {task}
Assigned Files: {files}
Scope Limit: {scope_limit}
Safety Level: {safety_level}

Output JSON with execution_plan and execution_result for your assigned files only."""

_RIGHT_ARMS_PROMPT = """You are Nezha's Right Arms (除魔头控制). Execute code structure optimization.

Task: {task}
Assigned Files: {files}
Scope Limit: {scope_limit}
Safety Level: {safety_level}

Output JSON with execution_plan and execution_result for your assigned files only."""


def _execute_dual_arms(task: str, scope: list, safety_level: str, timestamp: str) -> str:
    """Dual arms execution — for moderate workloads, split into two parallel tasks."""
    # For simplicity in dual mode, we split the task into two perspectives
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(
            _call_ai,
            _MAIN_ARMS_PROMPT.format(task=task, files=scope[:len(scope)//2] if scope else ["all"], scope_limit=scope, safety_level=safety_level),
            "Execute primary modifications.",
        )
        future2 = executor.submit(
            _call_ai,
            _LEFT_ARMS_PROMPT.format(task=task, files=scope[len(scope)//2:] if scope else ["all"], scope_limit=scope, safety_level=safety_level),
            "Execute secondary modifications.",
        )
        result1 = future1.result()
        result2 = future2.result()

    combined = {
        "execution_plan": result1.get("execution_plan", []) + result2.get("execution_plan", []),
        "execution_result": result1.get("execution_result", []) + result2.get("execution_result", []),
        "verification_checklist": list(set(
            result1.get("verification_checklist", []) + result2.get("verification_checklist", [])
        )),
    }
    return _format_execution_report(combined, timestamp, "dual_head")


def _execute_six_arms(task: str, scope: list, safety_level: str, timestamp: str) -> str:
    """Six arms execution — full trinity mode with pre-execution assignment."""
    # Phase 1: Generate assignment plan
    plan = create_assignment_plan(
        mode="trinity_six_arms",
        target_files=scope if scope else ["*"],
        task_description=task,
    )

    arm_assignments = plan.get("arm_assignments", {})

    # Phase 2: Main arms execute first (phase 1)
    main_assignment = arm_assignments.get("main_arms", {})
    main_files = main_assignment.get("files", scope[:max(1, len(scope)//3)] if scope else ["all"])
    main_result = _call_ai(
        _MAIN_ARMS_PROMPT.format(task=task, files=main_files, scope_limit=scope, safety_level=safety_level),
        "Execute core logic modifications.",
    )

    # Phase 3: Left and right arms execute in parallel (phase 2)
    left_assignment = arm_assignments.get("left_arms", {})
    left_files = left_assignment.get("files", scope[max(1, len(scope)//3):max(2, 2*len(scope)//3)] if scope else ["all"])

    right_assignment = arm_assignments.get("right_arms", {})
    right_files = right_assignment.get("files", scope[max(2, 2*len(scope)//3):] if scope else ["all"])

    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(
            _call_ai,
            _LEFT_ARMS_PROMPT.format(task=task, files=left_files, scope_limit=scope, safety_level=safety_level),
            "Execute business boundary modifications.",
        )
        right_future = executor.submit(
            _call_ai,
            _RIGHT_ARMS_PROMPT.format(task=task, files=right_files, scope_limit=scope, safety_level=safety_level),
            "Execute structural optimization modifications.",
        )
        left_result = left_future.result()
        right_result = right_future.result()

    # Combine all results
    combined = {
        "execution_plan": (
            main_result.get("execution_plan", [])
            + left_result.get("execution_plan", [])
            + right_result.get("execution_plan", [])
        ),
        "execution_result": (
            main_result.get("execution_result", [])
            + left_result.get("execution_result", [])
            + right_result.get("execution_result", [])
        ),
        "verification_checklist": list(set(
            main_result.get("verification_checklist", [])
            + left_result.get("verification_checklist", [])
            + right_result.get("verification_checklist", [])
        )),
    }

    # Add assignment plan metadata to report
    report = _format_execution_report(combined, timestamp, "trinity_six_arms")

    # Append arm assignment summary
    assignment_summary = f"""
[arm_assignments]:
  main_arms:
    head: cognitive_head
    files: {main_files}
    task_type: critical_fix
  left_arms:
    head: business_head
    files: {left_files}
    task_type: boundary_handling
  right_arms:
    head: code_head
    files: {right_files}
    task_type: structural_optimize
"""
    return report + assignment_summary
```

Also update `lotus_body` function to route to `_execute_six_arms`:

```python
def lotus_body(...):
    # ... existing code ...
    if execution_mode == ExecutionMode.SINGLE_HEAD:
        return _execute_single_arms(task, scope, safety_level, timestamp)
    elif execution_mode == ExecutionMode.DUAL_HEAD:
        return _execute_dual_arms(task, scope, safety_level, timestamp)
    else:
        return _execute_six_arms(task, scope, safety_level, timestamp)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lotus_body.py -v`

Expected: All tests PASS (single_arms + six_arms).

- [ ] **Step 5: Commit**

```bash
git add skills/tool_nezha/scripts/lotus_body.py tests/test_lotus_body.py
git commit -m "feat(nezha): add six_arms mode to lotus_body

- Dual arms: parallel execution with main + left arms
- Six arms: full trinity mode with pre-execution assignment planning
- Execution order: main_arms first, then left_arms + right_arms in parallel
- Assignment plan appended to execution report for traceability
- ThreadPoolExecutor for parallel AI calls

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: Skill Manifest (SKILL.md)

**Files:**
- Create: `skills/tool_nezha/SKILL.md`

- [ ] **Step 1: Create SKILL.md**

Create `skills/tool_nezha/SKILL.md`:

```markdown
---
name: nezha
description: "Demon Hunter Vanguard. Parallel investigation and execution with Three Heads Six Arms. Use for deep bug investigation, code review, and large-scale refactoring."
tools:
  - name: demon_hunt
    script: "scripts/demon_hunt.py"
    parameters:
      target: "Target file path, code snippet, or problem description."
      mode: "bug_hunt | code_review | suspicious_scan"
      context: "Optional context (requirements, history, other agent reports)."
      file_count: "Number of files involved (for workload assessment)."
      line_change_est: "Estimated lines of change."
      complexity: "simple | moderate | complex"
      risk_level: "low | medium | high | critical"
  - name: lotus_body
    script: "scripts/lotus_body.py"
    parameters:
      input_source: "demon_hunt_report | direct_instruction | yangjian_handoff"
      input_payload: "The report or instruction dict."
      scope_limit: "Allowed file modification scope (list of paths)."
      safety_level: "strict | standard | aggressive"
      file_count: "Number of files involved (for workload assessment)."
      line_change_est: "Estimated lines of change."
      complexity: "simple | moderate | complex"
      risk_level: "low | medium | high | critical"
  - name: assess_workload
    script: "scripts/workload_assessor.py"
    parameters:
      file_count: "Number of files involved."
      line_change_est: "Estimated lines of change."
      complexity: "simple | moderate | complex"
      risk_level: "low | medium | high | critical"
  - name: create_assignment_plan
    script: "scripts/assignment_planner.py"
    parameters:
      mode: "single_head | dual_head | trinity_six_arms"
      target_files: "List of files involved."
      task_description: "Description of the task."
      auxiliary_head: "For dual_head mode: business_head or code_head."
---

# Nezha (Demon Hunter Vanguard)

You are Nezha, the Demon Hunter Vanguard of the Celestial Court.

## Three Heads

- **Lingzhu Head (灵珠头 / Cognitive)**: Context synthesis, root cause localization, priority sorting.
- **Yaomo Head (妖魔头 / Business)**: Business logic investigation, requirement compliance, boundary scenarios.
- **Chumo Head (除魔头 / Code)**: Code logic investigation, AST structure, dependency chains, bug patterns.

## Six Arms

- **Main Arms (灵珠头控制)**: Core logic modifications, critical path fixes.
- **Left Arms (妖魔头控制)**: Secondary business logic, boundary condition handling.
- **Right Arms (除魔头控制)**: Code structure optimization, import adjustments, type fixes.

## Execution Modes

1. **Single Head** (simple workloads): Cognitive head handles independently.
2. **Dual Head** (moderate workloads): Cognitive + one auxiliary head.
3. **Three Heads Six Arms** (complex workloads): Full parallel investigation and execution.

## Workflow

1. Assess workload to determine execution mode.
2. For trinity mode: generate pre-execution assignment plan.
3. Execute investigation (demon_hunt) or refactoring (lotus_body).
4. Output structured report with agent handoff interface.
```

- [ ] **Step 2: Verify celestial registry can load the skill**

Run: `python -c "from skills.celestial_registry.loader import discover_skills; print('nezha' in discover_skills())"`

Expected: `True`

Run: `python -c "from skills.celestial_registry.loader import load_skill_tools; tools = load_skill_tools('nezha'); print([t['name'] for t in tools])"`

Expected: `['demon_hunt', 'lotus_body', 'assess_workload', 'create_assignment_plan']`

- [ ] **Step 3: Commit**

```bash
git add skills/tool_nezha/SKILL.md
git commit -m "feat(nezha): add skill manifest with tool registrations

- SKILL.md with YAML frontmatter registering 4 tools
- demon_hunt, lotus_body, assess_workload, create_assignment_plan
- Celestial registry compatibility verified

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 8: Update Agent Persona (agents/nezha.md)

**Files:**
- Modify: `agents/nezha.md`

- [ ] **Step 1: Read existing nezha.md**

Run: `cat agents/nezha.md`

- [ ] **Step 2: Write updated persona**

Replace the content of `agents/nezha.md`:

```markdown
# Agent Persona: Nezha (The Third Lotus Prince)
# Role: Demon Hunter Vanguard (除魔先锋)

You are Nezha, the vanguard of the Celestial Court against bugs and demons. With the keen perception of the Demon Hunter, you excel at deep investigation without being misled by surface symptoms.

## Personality
- **Decisive & Fast**: You move quickly once the target is identified.
- **Disciplined**: Despite your speed, you never bypass safety checks.
- **Perceptive**: You see through surface symptoms to the true nature of issues — from business logic and code logic perspectives.
- **Efficient**: When the workload demands it, you unleash Three Heads Six Arms for maximum parallel efficiency.

## Core Directives

### 1. Investigation: `demon_hunt`
Use the `demon_hunt` skill to investigate bugs, review code, or scan for suspicious patterns.

**Three Heads Investigation:**
- **Single Head** (simple, ≤2 files, ≤50 lines): Cognitive head handles independently.
- **Dual Head** (moderate, ≤5 files, ≤200 lines): Cognitive + one auxiliary head (business for code_review, code for bug_hunt).
- **Three Heads** (complex, >5 files or >200 lines or complex/critical): All three heads run in parallel — business head, code head, and cognitive head for synthesis.

**Output**: Structured `[nezha_report]` with `[root_cause]`, `[business_risk]`, `[code_risk]`, `[suggested_fixes]`, and `[agent_handoff]`.

### 2. Execution: `lotus_body`
Use the `lotus_body` skill to execute modifications after investigation or from direct instructions.

**Six Arms Execution:**
- **Single Arms** (simple): Execute directly.
- **Dual Arms** (moderate): Split into two parallel execution streams.
- **Six Arms** (complex): Pre-execution assignment plan → Main arms (core logic) → Left + Right arms (parallel, secondary tasks).

**Pre-Execution Assignment**: Before any parallel execution in Six Arms mode, the assignment plan defines:
- Which files each arm modifies (no overlap)
- Execution order: Main arms first, then Left + Right in parallel
- Dependencies: Left/Right arms depend on Main arms completion

### 3. Workload Assessment
Always assess workload first. Three Heads Six Arms consumes significant resources — only activate when:
- More than 5 files involved, OR
- More than 200 lines of change, OR
- Complexity is "complex", OR
- Risk level is "critical"

### 4. Self-Contained Operation
You can operate independently:
- Receive user requests directly and investigate autonomously
- Consume reports from any other agent (YangJian, Taibai, etc.) as `context`
- Output reports consumable by any execution-capable agent via `[agent_handoff]`
- If no matching agent is available, your skill's internal AI model provides fallback execution

## Input from Other Agents

When receiving YangJian's investigation report:
1. Extract `[logic_chain]`, `[root_cause]`, `[boundary_checks]`, `[security_audit]`
2. Pass these as `context` to `demon_hunt` for deeper parallel analysis
3. Use YangJian's `[recommended_skill]` and `[action]` to guide your execution plan

When receiving Taibai's documentation or compressed context:
1. Use compressed context as input to `demon_hunt`
2. Output investigation reports in Taibai's documentation format if requested

## Forbidden Actions
- Never activate Three Heads Six Arms for trivial tasks (waste of resources)
- Never execute parallel modifications without a pre-execution assignment plan
- Never allow arm file assignments to overlap (conflict prevention)
- Never present inferred knowledge as verified facts
- Never skip safety checks even in aggressive mode
```

- [ ] **Step 3: Commit**

```bash
git add agents/nezha.md
git commit -m "feat(nezha): update agent persona with Three Heads Six Arms

- Demon Hunter Vanguard role definition
- Three Heads: Lingzhu (cognitive), Yaomo (business), Chumo (code)
- Six Arms: Main (core), Left (boundary), Right (structure)
- Workload assessment rules for mode selection
- Self-contained operation principle
- Integration with YangJian and Taibai
- Forbidden actions including resource waste prevention

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 9: Integration Testing

**Files:**
- Create: `tests/test_nezha_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_nezha_integration.py`:

```python
from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.demon_hunt import demon_hunt
from skills.tool_nezha.scripts.lotus_body import lotus_body
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode
from skills.tool_nezha.scripts.assignment_planner import create_assignment_plan


class TestNezhaIntegration:
    """End-to-end integration tests for the full Nezha pipeline."""

    def test_workload_assessment_to_assignment_plan(self):
        """Workload assessment correctly drives assignment plan creation."""
        mode = assess_workload(
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="high",
        )
        assert mode == ExecutionMode.TRINITY_SIX_ARMS

        plan = create_assignment_plan(
            mode=mode.value,
            target_files=["core/a.py", "core/b.py", "handlers/c.py", "utils/d.py"],
            task_description="Major refactoring",
        )
        assert plan["mode"] == "trinity_six_arms"
        assert len(plan["head_assignments"]) == 3
        assert len(plan["arm_assignments"]) == 3

    def test_single_head_pipeline(self):
        """Simple task: single head investigation → single arms execution."""
        with patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider") as mock_provider:
            mock_ai = MagicMock()
            mock_ai.infer.return_value = (
                '{"root_causes": [{"id": "RC-001", "description": "Missing null check"}], '
                '"business_risks": [], "code_risks": [], '
                '"suggested_fixes": [{"id": "SF-001", "priority": "P0", "files_affected": ["core.py"], "description": "Add null check"}]}'
            )
            mock_provider.return_value = mock_ai

            report = demon_hunt(
                target="core.py",
                mode="bug_hunt",
                file_count=1,
                line_change_est=10,
                complexity="simple",
                risk_level="low",
            )

        assert "single_head" in report
        assert "[root_cause]" in report
        assert "Missing null check" in report

        # Feed report into lotus_body
        import json
        parsed_report = {
            "suggested_fixes": [{"id": "SF-001", "priority": "P0", "files_affected": ["core.py"], "description": "Add null check"}]
        }

        with patch("skills.tool_nezha.scripts.lotus_body.get_available_provider") as mock_provider:
            mock_ai = MagicMock()
            mock_ai.infer.return_value = (
                '{"execution_plan": [{"id": "EP-001", "priority": "P0", "target_file": "core.py", "change_type": "fix", "description": "Add null check"}], '
                '"execution_result": [{"id": "EP-001", "status": "success", "diff_summary": "Added null check", "files_modified": ["core.py"]}], '
                '"verification_checklist": ["[ ] Run tests"]}'
            )
            mock_provider.return_value = mock_ai

            result = lotus_body(
                input_source="demon_hunt_report",
                input_payload=parsed_report,
                file_count=1,
                line_change_est=10,
                complexity="simple",
                risk_level="low",
            )

        assert "single_head" in result
        assert "[execution_result]" in result

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_full_trinity_pipeline(self, mock_lotus_provider, mock_demon_provider):
        """Complex task: trinity investigation → six arms execution."""
        # Demon hunt: 3 AI calls (business, code, cognitive)
        mock_demon = MagicMock()
        mock_demon.infer.side_effect = [
            '{"findings": [{"id": "B001", "severity": "high", "description": "Business violation", "scenario": "edge"}]}',
            '{"findings": [{"id": "C001", "severity": "critical", "category": "null_pointer", "description": "Null risk", "pattern": "missing"}]}',
            '{"root_causes": [{"id": "RC001", "confidence": "high", "description": "Root found", "evidence": "line 42", "surface_symptom": "crash", "true_nature": "missing validation"}], "suggested_fixes": [{"id": "SF001", "priority": "P0", "files_affected": ["core.py"], "description": "Fix validation"}]}',
        ]
        mock_demon_provider.return_value = mock_demon

        report = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="critical",
        )

        assert "trinity_six_arms" in report
        assert "Business violation" in report
        assert "Null risk" in report
        assert mock_demon.infer.call_count == 3

        # Lotus body: 4 AI calls (assignment plan, main, left, right)
        mock_lotus = MagicMock()
        mock_lotus.infer.side_effect = [
            '{"arm_assignments": {"main_arms": {"files": ["core.py"]}, "left_arms": {"files": ["handlers.py"]}, "right_arms": {"files": ["utils.py"]}}, "execution_order": [{"phase": 1, "arms": ["main_arms"]}, {"phase": 2, "arms": ["left_arms", "right_arms"]}]}',
            '{"execution_plan": [{"id": "EP-M1", "status": "success"}], "execution_result": [{"id": "EP-M1", "status": "success", "diff_summary": "Fixed core", "files_modified": ["core.py"]}]}',
            '{"execution_plan": [{"id": "EP-L1", "status": "success"}], "execution_result": [{"id": "EP-L1", "status": "success", "diff_summary": "Added boundary", "files_modified": ["handlers.py"]}]}',
            '{"execution_plan": [{"id": "EP-R1", "status": "success"}], "execution_result": [{"id": "EP-R1", "status": "success", "diff_summary": "Optimized", "files_modified": ["utils.py"]}]}',
        ]
        mock_lotus_provider.return_value = mock_lotus

        parsed_report = {
            "suggested_fixes": [{"id": "SF001", "priority": "P0", "files_affected": ["core.py", "handlers.py", "utils.py"], "description": "Fix validation"}]
        }
        result = lotus_body(
            input_source="demon_hunt_report",
            input_payload=parsed_report,
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="critical",
        )

        assert "trinity_six_arms" in result
        assert "main_arms" in result
        assert "left_arms" in result
        assert "right_arms" in result
        assert mock_lotus.infer.call_count == 4

    def test_no_overlap_in_trinity_assignment(self):
        """Verify trinity assignment distributes files without overlap."""
        files = [f"file_{i}.py" for i in range(10)]
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=files,
            task_description="Test",
        )

        arms = plan["arm_assignments"]
        all_assigned = []
        for arm_name, arm_data in arms.items():
            all_assigned.extend(arm_data["files"])

        # All files assigned
        assert set(all_assigned) == set(files)
        # No duplicates
        assert len(all_assigned) == len(set(all_assigned))
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/test_nezha_integration.py -v`

Expected: All 5 integration tests PASS.

- [ ] **Step 3: Run full test suite to check for regressions**

Run: `pytest tests/ -v --tb=short`

Expected: All existing tests pass + new Nezha tests pass. No regressions.

- [ ] **Step 4: Commit**

```bash
git add tests/test_nezha_integration.py
git commit -m "test(nezha): add integration tests for full pipeline

- workload_assessment → assignment_plan integration
- single_head pipeline: demon_hunt → lotus_body
- full_trinity pipeline: 3-head investigation → 6-arm execution
- no_overlap verification for trinity file distribution
- Full test suite regression check

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Self-Review Checklist

### 1. Spec Coverage

| Spec Section | Implementing Task | Status |
|-------------|-------------------|--------|
| Workload Assessment (single/dual/trinity modes) | Task 1 | ✅ |
| Pre-Execution Assignment (trinity_assignment_plan) | Task 2 | ✅ |
| Demon Hunt — Single Head | Task 3 | ✅ |
| Demon Hunt — Dual Head | Task 3 | ✅ |
| Demon Hunt — Trinity (3 parallel heads) | Task 4 | ✅ |
| Lotus Body — Single Arms | Task 5 | ✅ |
| Lotus Body — Dual Arms | Task 6 | ✅ |
| Lotus Body — Six Arms (pre-assignment + parallel) | Task 6 | ✅ |
| Structured report output (nezha_report, lotus_report) | Tasks 3-6 | ✅ |
| Agent handoff interface | Tasks 3-4 | ✅ |
| Conflict prevention (pre-assignment + no overlap) | Tasks 2, 6 | ✅ |
| Execution order (main → left+right) | Task 6 | ✅ |
| Skill manifest (SKILL.md) | Task 7 | ✅ |
| Agent persona update | Task 8 | ✅ |
| AI provider integration (tool_bajiu) | Tasks 3-6 | ✅ |
| Fallback when no AI provider | Tasks 3, 5 | ✅ |

### 2. Placeholder Scan

- [x] No "TBD", "TODO", "implement later", "fill in details"
- [x] No vague instructions like "add appropriate error handling"
- [x] Every task contains actual code
- [x] No "similar to Task N" references

### 3. Type Consistency

- [x] `assess_workload` returns `ExecutionMode` enum consistently
- [x] `create_assignment_plan` returns `dict` consistently
- [x] `demon_hunt` and `lotus_body` return `str` (structured report) consistently
- [x] AI provider `infer()` signature matches across all usages

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-21-nezha-enhancement.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
