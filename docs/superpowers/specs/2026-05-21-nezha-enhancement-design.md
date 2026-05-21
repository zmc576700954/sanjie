# Nezha Agent Enhancement Design

**Date:** 2026-05-21
**Status:** Draft
**Author:** Claude

---

## 1. Overview

This document defines the enhanced capabilities for the **Nezha** Agent, transforming it from a "Rapid Responder & Surgical Executor" into a **Demon Hunter Vanguard** with parallel investigation and refactoring capabilities.

### Key Concepts

- **Three Heads (三头):** Parallel analysis from three perspectives — Business Logic, Code Logic, and Context Synthesis.
- **Six Arms (六臂):** Parallel execution of modifications — Main Arms for critical logic, Left Arms for secondary business logic, Right Arms for structural optimization.
- **On-Demand Activation:** Three Heads Six Arms is a "ultimate ability", not the default mode. Activated only when workload assessment determines high complexity.
- **Pre-Execution Assignment:** Work distribution happens **before** execution to prevent conflicts.

---

## 2. Core Positioning

### 2.1 Role: Demon Hunter Vanguard (除魔先锋)

Nezha is the Celestial Court's vanguard against bugs and demons. With keen perception of anomalies, Nezha excels at:

- Deep bug investigation without being misled by surface symptoms
- Code review with focus on business logic and code logic
- Efficient parallel execution leveraging the Three Heads Six Arms pattern

### 2.2 Three Heads Definition

| Head | Name | Responsibility | Focus Dimension |
|------|------|----------------|-----------------|
| **Main Head (Cognitive)** | 灵珠头 (Lingzhu) | Context synthesis, root cause localization, priority sorting, decision output | Mapping between business and code logic |
| **Left Head (Business)** | 妖魔头 (Yaomo) | Business logic investigation, requirement compliance, boundary scenarios, exception flows | User intent, business rules, data flows |
| **Right Head (Code)** | 除魔头 (Chumo) | Code logic investigation, AST structure, dependency chains, potential bug patterns | Syntax, semantics, performance, security patterns |

### 2.3 Six Arms Execution Mode

When entering the refactoring phase, each head controls two arms:

| Head | Arms | Scope |
|------|------|-------|
| **Lingzhu (Main)** | Main Arms | Core logic modifications, critical path fixes, root cause code changes |
| **Yaomo (Left)** | Left Arms | Secondary business logic, boundary condition handling, default values / config adjustments |
| **Chumo (Right)** | Right Arms | Code structure optimization, import adjustments, type fixes, formatting |

**Parallel Safety Constraint:** When three arms modify simultaneously, each must declare its **file scope** and **line range** to avoid conflicts.

---

## 3. Skill 1: `nezha_demon_hunt` (降魔眼)

### 3.1 Purpose

Receives target code / user request / review object. Internally launches 3 parallel AI subtasks (one per head). Outputs a structured investigation report.

### 3.2 Input Parameters

```yaml
target: str           # Target: file path, code snippet, or problem description
context: str          # Optional: related requirements, historical changes, YangJian investigation report
mode: enum            # "bug_hunt" | "code_review" | "suspicious_scan"
depth: enum           # "surface" | "deep" | "comprehensive" (default: deep)
```

### 3.3 Phase 0: Workload Assessment

Before activating any heads, the **Cognitive Head** performs workload assessment to determine execution mode:

```yaml
workload_assessment:
  criteria:
    file_count: int       # Number of files involved
    line_change_est: int  # Estimated lines of change
    complexity: enum      # "simple" | "moderate" | "complex"
    risk_level: enum      # "low" | "medium" | "high" | "critical"

  mode_selection:
    - condition: file_count <= 2 AND line_change_est <= 50 AND complexity == "simple"
      mode: "single_head"
      description: "Routine investigation/fix, no need to activate Three Heads"

    - condition: file_count <= 5 AND line_change_est <= 200 AND complexity == "moderate"
      mode: "dual_head"
      description: "Moderate complexity, Cognitive Head + one auxiliary head"
      auxiliary_selection: "Determined by mode: bug_hunt → code_head; code_review → business_head; suspicious_scan → both evaluated, higher relevance head selected"

    - condition: file_count > 5 OR line_change_est > 200 OR complexity == "complex" OR risk_level == "critical"
      mode: "trinity_six_arms"
      description: "High workload / high complexity / high risk — full Three Heads Six Arms"
```

### 3.4 Phase 1: Pre-Execution Assignment (Trinity Mode Only)

When mode is `trinity_six_arms`, the Cognitive Head outputs an assignment plan **before** execution:

```markdown
[trinity_assignment_plan]:
  mode: "trinity_six_arms"
  assessment_reason: "Involves 8 files, estimated 400+ line changes, core business logic refactoring"

  head_assignments:
    cognitive_head:
      role: "context_master"
      tasks:
        - "Parse global business context"
        - "Identify core vs secondary logic paths"
        - "Final root cause confirmation and priority sorting"
      deliverable: "[synthesis] + [priority_matrix]"

    business_head:
      role: "business_analyzer"
      tasks:
        - "Map business rules and boundary conditions"
        - "Verify requirement compliance"
        - "Identify exception flows and missing data validation"
      deliverable: "[business_risk] + [boundary_scenarios]"

    code_head:
      role: "code_analyzer"
      tasks:
        - "AST structure analysis"
        - "Dependency chain tracing"
        - "Bug pattern matching and security scanning"
      deliverable: "[code_risk] + [dependency_map]"
```

### 3.5 Phase 2: Parallel Investigation (Three Heads)

```
Input: target + context + assignment_plan (if trinity mode)
    │
    ├──→ [Business Head] AI subtask: Business logic analysis
    │       Output: [business_analysis]
    │       Contains: requirement compliance, boundary scenarios, exception flows, data validation points
    │
    ├──→ [Code Head] AI subtask: Code logic analysis
    │       Output: [code_analysis]
    │       Contains: AST risks, dependency chains, bug patterns, performance issues, security patterns
    │
    └──→ [Cognitive Head] AI subtask: Synthesis and root cause localization (depends on above two outputs)
            Output: [root_cause] + [synthesis]
```

### 3.6 Output Format: Structured Report

```markdown
[nezha_report]:
  timestamp: "YYYY-MM-DD HH:MM:SS"
  target: "<target>"
  mode: "<mode>"
  workload_assessment:
    file_count: 8
    line_change_est: 420
    complexity: "complex"
    risk_level: "high"
    execution_mode: "trinity_six_arms"

[root_cause]:
  - id: RC-001
    confidence: [high|medium|low]
    description: "Root cause description"
    evidence: "Code location or logic chain"
    surface_symptom: "Surface phenomenon"
    true_nature: "Essential problem"

[business_risk]:
  - id: BR-001
    severity: [critical|high|medium|low]
    location: "File:line"
    description: "Business logic risk"
    scenario: "Trigger scenario"
    impact: "Business impact"

[code_risk]:
  - id: CR-001
    severity: [critical|high|medium|low]
    location: "File:line"
    category: [null_pointer|injection|race_condition|performance|logic_error|type_mismatch|...]
    description: "Code-level risk"
    pattern: "Matched bug pattern"

[suggested_fixes]:
  - id: SF-001
    priority: [P0|P1|P2]
    related_risks: [BR-001, CR-001]
    description: "Fix recommendation"
    approach: "High-level approach"
    files_affected: ["file1", "file2"]

[agent_handoff]:
  # Reserved interface: consumable by any execution-capable agent
  recommended_executor: "execution-capable-agent"
  context_summary: "One-sentence summary"
  report_ref: "<report_id>"
```

---

## 4. Skill 2: `nezha_lotus_body` (莲花化身)

### 4.1 Purpose

Receives an investigation report or direct modification instruction. Internally distributes 3 parallel modification tasks (Six Arms). Outputs execution plan and modification results.

### 4.2 Input Parameters

```yaml
input_source: enum    # "demon_hunt_report" | "direct_instruction" | "yangjian_handoff"
input_payload: dict   # Output from demon_hunt, or direct instruction
scope_limit: list     # Allowed file modification scope (whitelist)
safety_level: enum    # "strict" (user confirmation required) | "standard" (auto execute + verify) | "aggressive" (maximum parallel)
```

### 4.3 Phase 0: Workload Assessment & Mode Selection

Same assessment criteria as `nezha_demon_hunt`. Only activates `trinity_six_arms` mode for large-scale modifications.

### 4.4 Phase 1: Pre-Execution Assignment (Trinity Mode)

When mode is `trinity_six_arms`, the Cognitive Head generates an arm assignment plan **before** any modifications:

```markdown
[trinity_assignment_plan]:
  mode: "trinity_six_arms"
  assessment_reason: "8 files involved, 400+ line changes, core logic refactoring"

  arm_assignments:
    main_arms:
      head: "cognitive_head"
      scope: "Core logic files"
      files: ["core/service.py", "core/model.py"]
      line_ranges: ["42-89", "120-156"]
      task_type: "critical_fix"
      description: "Fix root cause in core business logic"
      dependencies: []  # Main arms have no dependencies

    left_arms:
      head: "business_head"
      scope: "Secondary business logic + boundary handling"
      files: ["handlers/edge_cases.py", "config/defaults.py"]
      line_ranges: ["15-30", "5-12"]
      task_type: "boundary_handling"
      description: "Add boundary conditions, adjust defaults, improve exception handling"
      dependencies: ["main_arms"]  # Execute after main arms confirm interfaces

    right_arms:
      head: "code_head"
      scope: "Code structure optimization"
      files: ["utils/helpers.py", "tests/test_core.py"]
      line_ranges: ["1-45", "80-120"]
      task_type: "structural_optimize"
      description: "Optimize imports, fix type hints, supplement unit tests"
      dependencies: ["main_arms"]  # Execute after main arms confirm interfaces

  execution_order:
    - phase: 1
      arms: ["main_arms"]
      parallel: false
    - phase: 2
      arms: ["left_arms", "right_arms"]
      parallel: true

  conflict_prevention:
    - "All arms' line_ranges are declared before execution, no overlapping regions"
    - "If cross-file dependencies exist (e.g., right_arms need to modify a file declared by main_arms), auto-serialize"
    - "Execution order: main_arms → left_arms + right_arms (parallel)"
```

### 4.5 Phase 2: Parallel Execution (Six Arms)

```
Input: input_payload + assignment_plan
    │
    ├──→ [Parse Phase] Cognitive Head parses input, generates prioritized execution plan
    │       Output: [execution_plan] — sorted list of modification tasks
    │
    ├──→ [Phase 1: Main Arms Execute]
    │       main_arms execute P0 tasks (core logic)
    │       Declare: scope file + line range
    │
    ├──→ [Phase 2: Left + Right Arms Parallel Execute]
    │       left_arms execute P1 tasks (secondary business logic)
    │       right_arms execute P2 tasks (code structure)
    │       Both declare scope file + line range
    │
    └──→ [Verification Phase]
            ├── Conflict detection: Check if three arms' modifications overlap
            ├── Regression verification: Run related tests
            └── Output: [execution_result] + [verification_checklist]
```

### 4.6 Output Format

```markdown
[execution_plan]:
  - id: EP-001
    priority: P0
    owner: "main_arms"
    target_file: "path/to/file"
    line_range: "42-56"
    change_type: [fix|refactor|optimize]
    description: "Specific modification content"
    dependency_on: []

[execution_result]:
  - id: EP-001
    status: [success|failed|partial]
    diff_summary: "Change summary"
    files_modified: ["file1"]

[verification_checklist]:
  - [ ] Regression tests pass
  - [ ] Boundary condition verification
  - [ ] No dependency breakage
  - [ ] No performance degradation
  - [ ] Conflict detection passed

[lotus_report]:
  total_changes: 3
  success_rate: "100%"
  time_elapsed: "15s"
  next_steps: "Recommend running full test suite for verification"
```

### 4.7 Conflict Prevention Mechanism

```yaml
conflict_prevention:
  primary: "PRE_EXECUTION_ASSIGNMENT"
  # Pre-execution assignment is the primary conflict prevention method.
  # Each arm's file + line range is declared before execution.

  rules:
    - rule_1: "Before any arm modifies, it must declare file + line range. Overlapping regions auto-serialize."
    - rule_2: "P0 tasks in the same file take priority over P1/P2. P1/P2 execute after P0 completes."
    - rule_3: "If an unforeseen conflict is detected during execution, fall back to single-arm serial mode and log the reason."
```

---

## 5. Agent Responsibility Boundaries

| Agent | Core Responsibility | Relationship with Nezha |
|-------|---------------------|------------------------|
| **YangJian** | Root cause investigation, security audit, task routing | YangJian's investigation report can be provided as `context` input to `nezha_demon_hunt`. Nezha can work independently without depending on YangJian. |
| **Taibai** | Documentation management, context compression, A2A envelopes | Nezha's investigation reports can be archived through Taibai's GSSC pipeline. Taibai can compress long context for Nezha. |
| **Nezha** | Parallel investigation, precise refactoring, demon execution | Receives input from any source (user / YangJian / direct). Outputs investigation reports or executes modifications. |
| **WangLingGuan** | (To be defined) | — |

**Key Principle:** Nezha is **self-contained** — it can independently respond to user requests, or consume output from other agents, but does not require any prerequisite agent.

---

## 6. Tool / AI Model Integration Specification

### 6.1 Demon Hunt Internal Prompt Template

```markdown
# Role: Nezha's {{head_name}} Head
# Task: Analyze the following target from {{dimension}} perspective

## Input
Target: {{target}}
Context: {{context}}
Mode: {{mode}}

## Analysis Dimensions
{% if head == "business" %}
- Requirement compliance
- Business boundary scenarios
- Exception flow handling
- Data validation points
{% elif head == "code" %}
- AST structure risks
- Dependency chain analysis
- Bug pattern matching
- Performance issues
- Security pattern checks
{% elif head == "cognitive" %}
- Synthesize business_head and code_head outputs
- Identify root cause
- Priority sorting
- Decision output
{% endif %}

## Output Format
Strictly output in the following JSON:
{
  "findings": [...],
  "confidence": "...",
  "evidence": "..."
}
```

### 6.2 Lotus Body Internal Prompt Template

```markdown
# Role: Nezha's {{arms_name}} Arms
# Task: Execute the assigned modification task

## Assignment
Task ID: {{task_id}}
Priority: {{priority}}
Target: {{file}}:{{line_range}}
Change: {{description}}

## Safety Rules
- Declare scope before modifying
- Do not exceed scope_limit range
- Maintain consistent code style

## Output
{
  "status": "success|failed",
  "diff": "...",
  "conflicts": []
}
```

---

## 7. Execution Flow Summary

```
Input: target + context
    │
    ▼
[Phase 0: Workload Assessment]
    │
    ├── single_head (small workload)
    │     └── Cognitive Head handles independently
    │
    ├── dual_head (medium workload)
    │     └── Cognitive Head + one auxiliary head
    │
    └── trinity_six_arms (large workload)
          │
          ├── [Phase 1: Pre-Execution Assignment]
          │     Cognitive Head outputs [trinity_assignment_plan]
          │     Defines: each head's task boundary, each arm's file + line range, dependency order
          │
          ├── [Phase 2: Three Heads Parallel Investigation]
          │     Execute per assignment_plan, each head focuses on its own dimension
          │
          ├── [Phase 3: Cognitive Head Synthesis]
          │     Merge three heads' outputs → [nezha_report]
          │
          ├── [Phase 4: Six Arms Parallel Execution] (if modification needed)
          │     Execute strictly per assignment_plan's distribution
          │     main_arms execute first
          │     left_arms + right_arms execute in parallel after main_arms complete
          │
          └── [Phase 5: Verification]
                Conflict detection → Regression tests → Output [lotus_report]
```

---

## 8. Design Principles

| Principle | Description |
|-----------|-------------|
| **On-Demand Activation** | Three Heads Six Arms is not the default mode. Determined by Cognitive Head's workload assessment. |
| **Pre-Execution Assignment** | Assignment plan must be output before execution, defining each head/arm's boundary. |
| **Non-Overlapping Execution** | Each arm's `files + line_ranges` are determined before execution, no overlap in principle. |
| **Dependency Serialization** | If auxiliary arms depend on main arm's interface changes, auto-serialize (but ranges are still pre-declared). |
| **Fallback Safety** | If unforeseen conflicts are detected during execution, fall back to single-arm serial mode and log the reason. |
| **Self-Contained** | Nezha can work independently without requiring prerequisite agents. |
| **Hot-Pluggable** | Any agent matching the responsibility description can trigger Nezha's skills. No hard-coded agent names. |
