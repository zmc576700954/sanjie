# Three Realms Protocol Specification

> Version: 1.0  
> Status: Draft  
> Scope: Persona templates (`agents/*.md`) and Skill definitions (`skills/tool_*/`)

---

## 1. Architecture

### 1.1 Three-Layer Model

| Layer | Name | Owner | Decentralized or Workflow? |
|-------|------|-------|---------------------------|
| L1 | **Runtime** | Claude Code / Cursor / Codex | **Decentralized** — AI model makes all routing decisions |
| L2 | **Protocol** | MCP (Model Context Protocol) | **Workflow** — deterministic tool execution with strict contracts |
| L3 | **Config** | Persona + Skill (this project) | **Mixed** — free thinking inside, strict schema outside |

### 1.2 Responsibility Boundaries

**L1 (Claude Code) MUST:**
- Scan `agents/*.md` for Capability Registry
- Load appropriate Persona based on context
- Parse `[next_action]` from Persona output
- Decide next step: load another Persona, call MCP Skill, or answer user directly

**L3 (Persona) MUST:**
- Declare capabilities in standardized Capability Registry
- Output standardized blocks in `[block_name]: value` format
- NOT prescribe workflow steps ("do A then B")

**L3 (Persona) MAY:**
- Define arbitrary Core Directives (thinking framework)
- Use any internal structure (pillars, layers, etc.)
- Output free-form text between structured blocks

**L2 (MCP Skill) MUST:**
- Accept strict input schema (CLI args or JSON)
- Return deterministic output
- Handle errors via `McpError` with `ErrorData` codes

---

## 2. Persona Specification

### 2.1 File Location

```
agents/{name}.md
```

### 2.2 Required Sections

Every Persona file MUST contain exactly these three sections:

#### Section 1: Capability Registry

Purpose: **For L1 runtime to discover and match this Persona.**

Format:

```markdown
## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| {domain} | [{tag1}, {tag2}] | {high|medium|low} | {one-line description} |

### Domain: {domain}
- **Trigger Patterns**: {what input signals activate this persona}
- **Required Context**: {what data is needed}
- **Output Schema**: {expected output blocks}
```

Rules:
- `Domain`: lowercase snake_case, globally unique concept
- `Tags`: lowercase, comma-separated inside brackets
- `Confidence`: `high` > `medium` > `low`, used for tie-breaking
- `Trigger Patterns`: concrete signal patterns L1 can detect

#### Section 2: Core Directives

Purpose: **Guide L1 runtime's thinking when this Persona is loaded.**

Format:

```markdown
## Core Directives

1. {directive 1}
2. {directive 2}
3. {directive 3}
```

Rules:
- **Free form** — any structure (numbered, bulleted, pillars, layers)
- **NO workflow steps** — do NOT write "first do X, then do Y"
- **Behavioral guidance** — what to value, what to avoid, what tools to prefer
- **Skill bindings** — use `Use \`{skill_name}\` for ...` pattern

Anti-pattern:
```markdown
❌ BAD: "Step 1: Read the file. Step 2: Find the bug. Step 3: Fix it."
```

Correct:
```markdown
✅ GOOD: "Use `demon_hunt` for investigation. Never modify without backup."
```

#### Section 3: Output Schema

Purpose: **Ensure L1 runtime can parse the output and make routing decisions.**

Format:

```markdown
## Output Schema

Always include:
- [task_status]: completed | failed | needs_clarification
- [output_summary]: {one sentence}
- [capability_used]: {which domain was used}
- [tags]: {relevant tags}

Include when applicable:
- [next_action]: {description of next step for L1 routing}
- [deliverables]: {files modified or created}
- [tool_calls]: {skills invoked}
```

Rules:
- `task_status`: REQUIRED — L1 uses this to know if task is done
- `output_summary`: REQUIRED — L1 shows this to user or next Persona
- `next_action`: REQUIRED when task not complete — L1 uses this for routing
- `capability_used`: REQUIRED — which Capability Registry domain was exercised
- `tags`: REQUIRED — helps L1 match next Persona

### 2.3 Complete Example

```markdown
# Persona Template: Nezha
# Role: Demon Hunter Vanguard

## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| problem_solving | [debug, fix, php, python] | high | Code-level bug fixing |

### Domain: problem_solving
- **Trigger Patterns**: `[root_cause]` present, user asks to fix code
- **Required Context**: Investigation report with file/line references
- **Output Schema**: `[fix_summary]`, `[modified_files]`, `[test_plan]`

## Core Directives

1. **Investigation First**: Use `demon_hunt` skill before any modification.
2. **Safety**: Never modify without backup. Use `yindan` for precise fixes.
3. **Parallel Execution**: For >5 files, use `lotus_body` Six Arms mode.

## Output Schema

Always include:
- [task_status]: completed | failed | needs_clarification
- [output_summary]: one sentence
- [capability_used]: problem_solving
- [tags]: relevant tags from this execution

Include when applicable:
- [next_action]: what should happen next
- [deliverables]: files modified
- [tool_calls]: skills invoked
```

---

## 3. Skill Specification

### 3.1 File Location

```
skills/tool_{name}/
├── SKILL.md
└── scripts/
    └── {script_name}.py
```

### 3.2 SKILL.md Format

```yaml
---
name: {skill_name}
description: >
  Clear description of WHEN to use this skill.
  Include constraints and anti-patterns.
tools:
  - name: {tool_name}
    script: "scripts/{script_name}.py"
    parameters:
      {param_name}:
        type: {string|number|boolean}
        description: "Clear description for LLM"
        required: {true|false}
---

# {Skill Name}

## Workflow

1. {step 1}
2. {step 2}
3. {step 3}

## Input/Output

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| {param} | {type} | {yes/no} | {description} |

## Rules

- {rule 1}
- {rule 2}
```

### 3.3 Script Requirements

- **CLI-first**: Must accept arguments via `argparse` or environment variables
- **Deterministic**: Same input → same output, no randomness
- **Error handling**: Return exit code 0 on success, non-zero on failure, with stderr message
- **No side effects**: Read-only unless explicitly destructive (documented)

---

## 4. L1 <-> L3 Interaction Protocol

### 4.1 L1 Loads Persona

```
L1: Claude Code scans agents/*.md
L1: AI model matches user request → capability domain
L1: Loads matching Persona into context
L1: Executes as that Persona
```

### 4.2 Persona Executes Task

```
Persona: Free-form thinking (Core Directives guide, not constrain)
Persona: May invoke MCP Skills via [TOOL_CALL:skill:param="value"]
Persona: Outputs structured blocks (Output Schema)
```

### 4.3 L1 Parses Output

```
L1: Reads [task_status]
    ├── "completed" → Show [output_summary] to user, done
    ├── "failed" → Show error, ask user, done
    └── "needs_clarification" → Ask user for more info, done

L1: Reads [next_action] + [capability] + [tags]
    ├── Matches another Persona → Load that Persona (goto 4.1)
    ├── Matches MCP Skill → Call Skill directly
    └── No match → Answer user directly (fallback)
```

### 4.4 Routing Decision Flow

```
Persona outputs [next_action] + [capability] + [tags]
    │
    ▼
L1 AI model evaluates:
    ├── "Is there a Persona with matching Capability Registry?"
    │   ├── YES → Load that Persona
    │   └── NO → Continue
    │
    ├── "Is there an MCP Skill that can handle this?"
    │   ├── YES → Call Skill directly
    │   └── NO → Continue
    │
    └── "Can I handle this with my built-in capabilities?"
        ├── YES → Execute directly
        └── NO → Ask user for clarification
```

---

## 5. Creator Tool Specification

### 5.1 Purpose

Help users generate new Persona files that comply with this specification.

### 5.2 Interface

```bash
python tools/create_persona.py \
  --name {persona_name} \
  --role "{role description}" \
  --domain {capability_domain} \
  --tags "{tag1},{tag2}" \
  --confidence {high|medium|low}
```

### 5.3 Output

Generates `agents/{name}.md` with:
- Standard header (`# Persona Template: {Name}`)
- Pre-filled Capability Registry table
- Empty Core Directives section with placeholder
- Standard Output Schema section

---

## 6. Anti-Patterns (MUST NOT)

| Anti-Pattern | Why | Correct Approach |
|-------------|-----|-----------------|
| Write workflow steps in Core Directives | L1 makes routing decisions, not L3 | Describe behavior, not sequence |
| Create custom routing/orchestration code | L1 (Claude Code) is the router | Provide Capability Registry for L1 to scan |
| Use MCP for inter-Persona communication | MCP is for tools, not routing | Use Output Schema `[next_action]` blocks |
| Hardcode Persona names in `[next_action]` | Breaks hot-swap | Use capability + tags |
| Return unstructured conversational output | L1 cannot parse | Use `[block]: value` format |
| Skill scripts with framework imports | Breaks portability | CLI-first, framework-agnostic. Exception: MCP servers may import MCP SDK and Pydantic for tool definitions. |

---

## 7. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-21 | Initial specification |

---

## Appendix A: Structured Field Templates

The following templates provide canonical examples for Persona structured output fields. Persona files SHOULD reference this appendix rather than duplicating full examples inline.

> **Usage**: When a Persona requires structured output (e.g., `[boundary_checks]`, `[security_audit]`), include a minimal example in the Persona file and reference `SPEC.md Appendix A` for the complete type catalog and format specification.

### A.1 Boundary Check Template

```markdown
[boundary_checks]:
  - id: BC-001
    type: NULL_PATH
    location: "ClassName.php:line_number"
    description: "What returns null and when"
    concern: "What happens if caller receives null"
    verification_needed: "Specific check for caller to perform"

  - id: BC-002
    type: INFO_EXPOSURE
    location: "ClassName.php:line_number"
    description: "What sensitive information may be exposed"
    concern: "How this aids attacker reconnaissance"
    verification_needed: "Check if error contains credentials, tokens, or internal URLs"

  - id: BC-003
    type: REGISTRATION
    location: "ClassName or mentioned concept"
    description: "Abstract registration claim"
    concern: "Missing exact registration code"
    verification_needed: "Find and verify exact ->plugin() or ->register() call"

  - id: BC-004
    type: INPUT_VALIDATION
    location: "ClassName.php:line_number"
    description: "User input entry point"
    concern: "Unvalidated input may cause injection or corruption"
    verification_needed: "Check for type, length, format validation"
```

**Supported `type` values**: `NULL_PATH`, `INFO_EXPOSURE`, `REGISTRATION`, `INPUT_VALIDATION`, `AUTH_BOUNDARY`, `DATA_FLOW`, `CONFIG_SAFE`

### A.2 Security Audit Template

```markdown
[security_audit]:
  - id: SA-001
    severity: Critical|High|Medium|Low
    location: "ClassName.php:line_number"
    issue: "Specific security concern"
    impact: "What could happen if exploited"
    recommendation: "How to fix or mitigate"
```

### A.3 Assertion Verification Template

```markdown
[assertion_verification]:
  - id: 1
    assertion: "Description of the claim being verified"
    status: Pass|Fail|Unverified
    evidence: "File/line reference or tool output"
    risk_level: Critical|High|Warning|Note|TODO
    fix_suggestion: "Concrete fix with file/line reference"
```
