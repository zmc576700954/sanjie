# Three Realms (三界): AI-Native Development Protocol

This document defines the core engineering standards and architectural philosophy for the `agents_develop` project. All future personas, skills, and tools developed in this workspace MUST adhere to these principles.

> **Positioning**: This project operates at **L3 (Config Level)**. We do not build Agent runtimes (L1) or protocols (L2). We provide **Persona templates** and **Skill definitions** that host Agent runtimes (Claude Code, Cursor, Codex, etc.) consume to alter their behavior.
>
> **Implementation note**: The Python package (`src/agents_develop/`) adds an optional **L1 Orchestrator** layer (`orchestrator.py` + `skill_bridge.py`) for standalone usage. This does not replace the L3 Config approach — when used inside Claude Code, the host runtime (Claude Code) handles routing directly via Persona Capability Registry. The Orchestrator is a convenience layer for CLI/SDK usage outside of Claude Code.

---

## What We Do vs What We Don't

### ❌ We Do NOT

| Don't | Why |
|-------|-----|
| **Replace host Agent runtimes** | Claude Code / Cursor are already the best ReAct runtimes |
| **Hardcode workflow in Personas** | L1 decides execution order via AI model |
| **Create custom protocols** | MCP is the standard tool protocol; we use it, don't replace it |
| **Prescribe workflows in Personas** | "Do A then B" violates decentralization; let L1 decide order |
| **Build message queues or routers** | L1 reads `[next_action]` and decides; no middleware needed |

### ✅ We DO

| Do | Purpose |
|----|---------|
| **Define Persona format** | Standardized Capability Registry + Output Schema for L1 discovery |
| **Provide example Personas** | Show how the format works in practice (Nezha, Taibai, etc.) |
| **Provide Creator tools** | `tools/create_persona.py` helps users generate compliant Personas |
| **Define Skill format** | Standardized SKILL.md + deterministic scripts for MCP |
| **Provide MCP Server suite** | Common tools (file ops, git, test runner) as reusable L2 bricks |
| **Validate the hypothesis** | Test: does Claude Code reliably route via `[next_action]`? |

---

## 1. Absolute Decentralization (No Python Orchestrators)

**Anti-Pattern:** Using a central Python class to instantiate personas and hardcode their sequential workflow.

**Three Realms Standard:**
- **Zero Central Logic:** Personas (`agents/*.md`) and Skills (`skills/tool_*/`) must be entirely decoupled. There is no `main.py` orchestrating them.
- **L1 Runtime Routing:** Claude Code (or Cursor, Codex) loads the appropriate persona by scanning Capability Registry and using its AI model to match.
- **Autonomous Handoff:** Personas output structured blocks (e.g., `[next_action]: ...`). L1 reads these and decides the next step — load another persona, call an MCP skill, or answer the user directly.

## 2. MCP-First Tool Design (Deterministic Execution)

**Anti-Pattern:** Writing Python scripts tightly coupled to our specific framework's internal imports.

**Three Realms Standard:**
- Scripts inside `skills/tool_*/scripts/` must be **CLI-first**, taking clear arguments or JSON input, returning JSON or Markdown.
- MCP Servers in `mcp-servers/` provide deterministic tool execution with strict `pydantic` schemas.
- Skills are **workflow** (deterministic), not **decentralized** — same input always produces same output.

## 3. Strict Prompt-Level Tool Protocols

**Anti-Pattern:** Vague instructions like "use the search tool" leading to LLM hallucinations.

**Three Realms Standard:**
- Every Persona MUST contain exact tool invocation formats with few-shot examples.
- Example: `To search local logic, output exactly: [TOOL_CALL:logic_tracer:error_desc="null pointer"]`
- This ensures the persona's raw text output deterministically triggers tool execution.

## 4. Schema Enforcement for Output (The Handoff Contract)

**Anti-Pattern:** Unstructured conversational text between personas, causing context loss.

**Three Realms Standard:**
- Every Persona MUST output standardized blocks in `[block_name]: value` format.
- Required blocks: `[task_status]`, `[output_summary]`, `[capability_used]`, `[tags]`
- Optional but critical: `[next_action]` — L1 uses this for routing decisions.
- This structured text is the "API" between decentralized personas.

## 5. Free-Thinking Core Directives (No Workflow Steps)

**Anti-Pattern:** Writing "Step 1: Read file. Step 2: Find bug. Step 3: Fix it." in Personas.

**Three Realms Standard:**
- Core Directives describe **behavior** (what to value, what to avoid, preferred tools).
- Core Directives do NOT prescribe **sequence** (let L1 decide order).
- Personas may use any internal structure (pillars, layers, rules) — completely free.

## 6. Capability-Based Discovery (No Hardcoded Names)

**Anti-Pattern:** Hardcoding persona names ("call Nezha") in routing logic.

**Three Realms Standard:**
- Personas declare capabilities in `## Capability Registry` (domain, tags, confidence).
- L1 scans these declarations and matches by capability + tags, not by name.
- Replacing Nezha with JinZha requires zero changes — just swap the `.md` file.

## 7. Skill Evaluation & Quality Assurance

**Anti-Pattern:** Developing skills without verifying tool execution accuracy.

**Three Realms Standard:**
- Every new Skill MUST have unit tests in `tests/test_{skill_name}.py`.
- Evaluation: can a persona reliably trigger this skill using only its Markdown prompt?

## 8. MCP Server Security & Schema Standards

**Anti-Pattern:** Raw parameters without descriptions, string error messages, trusting LLM-provided paths.

**Three Realms Standard:**
- All MCP tools use `pydantic.Field` for exhaustive parameter descriptions.
- Tools raise `mcp.shared.exceptions.McpError` with proper `ErrorData` codes.
- Filesystem tools validate paths via `utils.ensure_safe_path` to prevent traversal attacks.

## 9. Creator Tool Standard

**Anti-Pattern:** Hand-writing Persona files from scratch, leading to inconsistent formats.

**Three Realms Standard:**
- Use `python tools/create_persona.py --name ... --role ...` to generate compliant templates.
- Creator tool generates: standard header, Capability Registry table, empty Core Directives, Output Schema.
- Users fill in the blanks, ensuring all required sections are present.

---

## Current Project Layout

```
agents/
  yangjian.md, nezha.md, wanglingguan.md, taibai.md, jinzha.md   ← L3 Persona 定义

skills/tool_*/
  SKILL.md + scripts/                                             ← L3 Skill 定义

mcp-servers/
  taibai_server.py, tianyan_server.py, ...                        ← MCP Server（L2 工具层）

src/agents_develop/                                               ← Python 包（可选 L1 编排层）
  orchestrator.py     ← 管线编排（investigate → fix → review）
  skill_bridge.py     ← 关键词路由注册表（9 个 Skill）
  agents/             ← SubAgent 实现（investigator, fixer, reviewer, documenter）
  tools/              ← 工具封装（code_analysis, security_scan, code_modification, doc_tools）
  schemas.py          ← Pydantic I/O + AgentHandoff + TokenBudget + TracingSpan

a2a_inbox/review_tickets/                                         ← Agent-to-Agent 审查工单
tools/create_persona.py                                           ← Persona 模板生成器
```

**两种使用方式：**

1. **在 Claude Code 中使用**：Claude Code 作为 L1 Runtime，直接读取 `agents/*.md` 和 `skills/tool_*/SKILL.md`，通过 Capability Registry 自主路由
2. **独立 CLI/SDK 使用**：通过 `agents` CLI 命令或 Python SDK 调用 Orchestrator 编排层

---

## Conclusion for Contributors

When working on this project:
1. **Persona/Skill 层**：不写运行时编排逻辑 — Personas 和 Skills 保持解耦，供 L1 Runtime 自由路由
2. **Orchestrator 层**（可选）：`src/agents_develop/` 中的编排代码是 CLI/SDK 便利层，不影响 L3 Config 的使用方式
3. **Never** put workflow steps in Personas — describe behavior, not sequence.
4. **Always** use the Creator tool for new Personas — ensures format compliance.
5. **Always** write unit tests for new Skills — ensures deterministic execution.
6. **Always** use capability-based descriptions in `[next_action]` — enables hot-swapping.
