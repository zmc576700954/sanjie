# Three Realms (三界): AI-Native Development Protocol

This document defines the core engineering standards and architectural philosophy for the `agents_develop` project. All future agents, skills, and tools developed in this workspace MUST adhere to these principles.

## 1. Absolute Decentralization (No Python Orchestrators)
**Anti-Pattern:** Using a central Python class (like `MultiAgentTripPlanner`) to instantiate agents and hardcode their sequential workflow.
**Three Realms Standard:**
- **Zero Central Logic:** Agents (`agents/*.md`) and Skills (`skills/tool_*/`) must be entirely decoupled. There is no `main.py` orchestrating them.
- **CLI/Host Routing:** Rely exclusively on the host CLI (Claude Code, Gemini CLI, Cursor) to load the appropriate agent based on file metadata (`description`).
- **Autonomous Handoff:** Agents orchestrate workflows by writing structured text instructions in their output (e.g., `[Action Required]: Wake up $nezha to fix this`), handing control back to the user or the CLI host, not by invoking Python functions.

## 2. MCP-First Tool Design (Universal Accessibility)
**Anti-Pattern:** Writing Python scripts tightly coupled to our specific framework's internal imports, making them unusable outside our exact setup.
**Three Realms Standard:**
- Treat the `skills/` directory not just as local scripts, but as potential **Model Context Protocol (MCP)** servers.
- Scripts inside `skills/tool_*/scripts/` must be highly cohesive, taking clear CLI arguments or standard JSON input, returning standard JSON or Markdown output.
- Future tool development (like TianYan's Code Graph or Taibai's Compressor) should prioritize being wrapped as standard MCP servers, allowing them to be consumed by any modern AI IDE instantly.

## 3. Strict Prompt-Level Tool Protocols (Zero-Code Reliability)
**Anti-Pattern:** Vague instructions like "use the search tool to find the bug" which leads to LLM hallucinations and malformed tool calls.
**Three Realms Standard:**
- Every Agent Persona (`agents/*.md`) MUST contain a `<Celestial Protocol>` section defining exact tool invocation formats.
- **Use Few-Shot Examples:** Explicitly show how to call tools.
  *Example:*
  `To search local logic, you MUST output exactly: [TOOL_CALL:logic_tracer:error_desc="null pointer"]`
- This ensures that even without a heavy Python parser, the agent's raw text output deterministically triggers the correct actions.

## 4. Schema Enforcement for Output (The Documentation Guard)
**Anti-Pattern:** Allowing agents to output unstructured, conversational text when passing data to the next agent or writing documentation.
**Three Realms Standard:**
- Agents like Taibai must enforce rigid Data Schemas.
- When generating files, force the inclusion of YAML Frontmatter (`title`, `status`, `date`).
- When passing context to another agent, use fenced, standardized blocks:
  ```
  [logic_chain]: ...
  [root_cause]: ...
  [recommended_skill]: ...
  ```
- This structured text acts as the "API" between decentralized agents, replacing Python object passing.

## 5. Agentic Memory Pipeline (The GSSC Framework)
**Anti-Pattern:** Treating memory simply as saving text files or piling everything into `AGENTS.md`, leading to immediate context window bloat.
**Three Realms Standard:**
- Memory must be structured across four dimensions: Procedural (Skills), Semantic (Architecture), Episodic (History), and Working (Current task).
- Agents responsible for documentation and context MUST utilize the **GSSC Pipeline**: 
  - **G**ather (collect logs/conversations)
  - **S**elect (filter out noise)
  - **S**tructure (apply YAML/Markdown schemas)
  - **C**ompress (use compression tools to shrink tokens before saving).

## 6. A2A (Agent-to-Agent) Text-Based Handoff Protocol
**Anti-Pattern:** Users copying a conversational response from one agent and pasting it to another, causing the receiving agent to lose focus due to conversational filler.
**Three Realms Standard:**
- Agents MUST communicate across the decentralized cluster using a **Data Envelope** format.
- When an agent suggests invoking another agent (e.g., YangJian calling Nezha), it MUST generate a standardized markdown block:
  ```markdown
  ```json A2A_HANDOFF
  {
    "target_agent": "nezha",
    "context_pointers": ["docs/MEMORY_INDEX.md"],
    "actionable_spec": "..."
  }
  ```
- Receiving agents are instructed via their `<Celestial Protocol>` to prioritize reading data inside the `A2A_HANDOFF` block over user conversation.

## 7. Skill Evaluation & Quality Assurance
**Anti-Pattern:** Developing tools and skills without verifiable metrics on how well the host CLI (Claude Code/Codex) handles the tool invocation.
**Three Realms Standard:**
- Every new Skill MUST be verifiable via an Evaluator persona or script.
- Evaluation focuses on **Tool Execution Accuracy** and **Formatting Compliance** (LLM-as-a-Judge methodology).
- We maintain quality by testing if an agent can reliably trigger the new tool using only its Markdown prompt in a zero-shot or few-shot scenario.

## 8. MCP Server Security & Schema Standards (Production Readiness)
**Anti-Pattern:** Writing raw Python parameters without descriptions, returning text strings for errors, and trusting raw file paths from LLMs.
**Three Realms Standard:**
- **Strict Schemas:** All MCP tools MUST use `pydantic.Field` to provide exhaustive descriptions for every parameter. This prevents LLM hallucinations (e.g., specifying that text replacements must be exact literal matches).
- **Native Error Handling:** Tools MUST raise `mcp.shared.exceptions.McpError` (with appropriate `ErrorData` codes like `INTERNAL_ERROR` or `INVALID_PARAMS`) instead of returning error string messages. This enables the client IDE to trigger automatic self-correction.
- **Path Security (Sandbox):** Any tool that reads or writes to the filesystem MUST validate the target path using a centralized utility (e.g., `utils.ensure_safe_path`). The path must be absolute and strictly constrained within the workspace root to prevent directory traversal attacks.

## Conclusion for AI Assistants
When asked to create a new Agent or a new Skill in this project:
1. **Never** create a central Python orchestrator.
2. **Always** define the agent as a standalone Markdown file.
3. **Always** define tools as standalone scripts with strict input/output formats, ready for MCP encapsulation.
4. **Always** write strict, few-shot prompt protocols for inter-agent communication.
