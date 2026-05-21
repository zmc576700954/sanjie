# Taibai Enhancement Design

## Overview

Enhance the Taibai (太白金星) agent across three dimensions: tool visibility, A2A protocol integration, and review toolization. Follow the conservative incremental approach (方案 1): each phase adds minimal necessary changes, with regression testing after every phase and comprehensive validation at the end.

**Key constraint**: Reduce hard-coded agent coupling. Review capability is exposed through tool calls, not by naming specific agents like WangLingGuan.

---

## Phase A: Tool Visibility (GSSC Pipeline Completion)

### Problem

The GSSC pipeline scripts (`gather.py`, `select.py`, `structure.py`, `gssc_pipeline.py`) are fully implemented and tested, but:

1. `skills/tool_taibai/SKILL.md` only declares 2 tools (`archive_manager`, `context_compressor`) — the 4 GSSC tools are invisible to auto-discovery.
2. `agents/taibai.md` mentions GSSC conceptually (Pillar 5) but provides no concrete tool invocation guidance.
3. `skills/agent_taibai/SKILL.md` is a disconnected stub.
4. `mcp-servers/taibai_server.py` only registers 2 MCP tools.

### Changes

#### A1. Update `skills/tool_taibai/SKILL.md`

Add 4 new tool declarations while keeping the existing 2:

- **gather**: `source_paths` (list[str]), `patterns` (optional list[str])
- **select**: `raw_sources` (dict), `noise_patterns` (optional list[str]), `keep_sections` (optional list[str])
- **structure**: `selected_sources` (dict), `doc_type` (str), `author` (str), `metadata` (optional dict)
- **gssc_pipeline**: `source_paths` (list[str]), `doc_type` (str), `aggressive_compress` (bool), `output_path` (optional str), `author` (str)

Keep existing:
- **archive_manager**: `file`, `topic`, `summary`
- **context_compressor**: `file`, `aggressive`

#### A2. Update `agents/taibai.md`

In Pillar 5, replace the conceptual 4-step list with a concrete "Tool Invocation Sequence" subsection:

- **One-shot mode**: Use `gssc_pipeline` when you want the full pipeline in a single call. Provide `source_paths`, `doc_type`, and optionally `output_path`.
- **Step-by-step mode**: Use individual tools when you need to inspect intermediate results or inject custom `noise_patterns` / `metadata`.
  1. `gather` → collect sources
  2. `select` → filter noise
  3. `structure` → inject YAML frontmatter and Markdown sections
  4. `context_compressor` → compress the structured output

Add call examples for both modes.

#### A3. Update `skills/agent_taibai/SKILL.md`

Replace the stub with a lightweight but accurate description:
- Role: Context Manager & Documentation Specialist
- Capabilities: GSSC pipeline, archiving, context compression
- Reference: delegates to `tool_taibai` for actual execution

#### A4. Update `mcp-servers/taibai_server.py`

Register 4 new MCP tools mapping to the GSSC functions:
- `gather_sources` → wraps `gather_sources()`
- `select_content` → wraps `select_content()`
- `structure_document` → wraps `structure_document()`
- `run_gssc_pipeline` → wraps `run_pipeline()`

Each tool uses pydantic `Field` descriptions matching the SKILL.md declarations.

### Regression Validation

Run existing test suite:
```bash
pytest tests/test_gssc_pipeline.py tests/test_archive_manager.py tests/test_context_compressor.py -v
```
All tests must pass before proceeding to Phase B.

---

## Phase B: A2A Protocol Layer

### Problem

A2A infrastructure (`a2a_utils.py`, `a2a_inbox/` directory) exists and is tested, but no agent persona instructs the LLM to use it. Taibai's persona has no A2A awareness.

### Changes

#### B1. Update `agents/taibai.md`

Add a new section "A2A Envelope Protocol" after Pillar 5:

- **When to use**: When Taibai needs to hand off structured context to another agent, or when receiving a handoff from another agent.
- **Writing envelopes**: Call `write_envelope` with a dictionary containing:
  - `message_type`: "handoff" | "request" | "response"
  - `payload`: The actual content (context summary, document reference, etc.)
  - `priority`: "high" | "normal" | "low"
  - Optional: `from`, `to` — but **do not hard-code target agents**. Use descriptive roles (e.g., `"to": "review-capable-agent"`) and let the scheduler resolve.
- **Reading envelopes**: Call `read_envelope_for_agent(agent_name="taibai")` to poll for pending messages.
- **Envelope content rules**: Always include a `document_ref` field pointing to the structured document path when handing off documentation tasks.

#### B2. Interface Compatibility Check

Verify `a2a_utils.py` signatures match the usage patterns described in the persona:
- `write_envelope(envelope: dict, inbox_dir: str = "a2a_inbox") -> str`
- `read_envelope_for_agent(agent_name: str, inbox_dir: str = "a2a_inbox") -> dict | None`

Both are compatible. No code changes needed in `a2a_utils.py`.

### Regression Validation

Run A2A tests:
```bash
pytest tests/test_a2a_inbox.py -v
```

---

## Phase C: Review Toolization

### Problem

Taibai's persona references WangLingGuan directly in the old handoff flow. The user wants review capability decoupled from specific agents.

### Changes

#### C1. New Tool: `skills/tool_taibai/scripts/review_request.py`

```python
def request_review(
    document_path: str,
    review_type: str = "format",  # "format" | "quality" | "assertion" | "architecture"
    context_notes: str = "",
) -> dict:
    """Submit a document for review.

    Args:
        document_path: Path to the document to review.
        review_type: Category of review requested.
        context_notes: Additional context for the reviewer.

    Returns:
        dict with review_ticket_id, status, estimated_turnaround.
    """
```

Implementation:
- Validate document exists and is readable.
- Generate a ticket ID (UUID short form).
- Write a review request envelope to `a2a_inbox/pending/` using `write_envelope`.
- The envelope `to` field is set to `"review-pool"` (scheduler resolves the actual agent).
- Return ticket metadata.

#### C2. Update `skills/tool_taibai/SKILL.md`

Add `review_request` tool declaration:
- `document_path`: Path to the document.
- `review_type`: One of "format", "quality", "assertion", "architecture".
- `context_notes`: Optional context.

#### C3. Update `agents/taibai.md`

Replace the old "Input from YangJian" section's implicit WangLingGuan references with a new "Review Workflow" section:

- After completing any technical document, Taibai **must** evaluate whether it needs review based on:
  - Presence of `[unverified]` assertions
  - Risk severity grading includes Critical or High
  - Document type is "spec" or "handoff"
- If review is needed, call `request_review` with appropriate `review_type`.
- Do **not** specify which agent performs the review. The scheduler assigns from the review-capable pool.
- When receiving review feedback (via A2A inbox), incorporate changes and update the document's `status` frontmatter field accordingly.

Remove or soften the WangLingGuan-specific language in the "Input from YangJian" section. Keep the data format descriptions (`[logic_chain]`, `[root_cause]`, etc.) but remove phrases like "submit to WangLingGuan".

#### C4. Update `mcp-servers/taibai_server.py`

Register `request_review` as an MCP tool.

### Regression Validation

1. Run full test suite: `pytest tests/ -v`
2. Verify `request_review` generates correct A2A envelopes in `a2a_inbox/pending/`.
3. Verify no hard-coded agent names appear in Taibai's persona.

---

## MCP Server Synchronization

After each phase, update `mcp-servers/taibai_server.py` to register new tools. Final state:

| MCP Tool | Source Function | Phase |
|----------|----------------|-------|
| `compress_context` | `ContextCompressor.compress()` | Existing |
| `archive_document` | `archive_file()` | Existing |
| `gather_sources` | `gather_sources()` | A |
| `select_content` | `select_content()` | A |
| `structure_document` | `structure_document()` | A |
| `run_gssc_pipeline` | `run_pipeline()` | A |
| `request_review` | `request_review()` | C |

---

## Comprehensive Validation: 100-Task Test Suite

After all phases, run a comprehensive validation. The 100 tasks are organized into 5 categories:

### Category 1: GSSC Pipeline (30 tasks)

Tests gather, select, structure, compress, and full pipeline under various inputs:
1. Gather single file
2. Gather directory with pattern
3. Gather directory without pattern
4. Gather nonexistent path (error handling)
5. Gather empty directory
6. Gather binary file (should skip)
7. Gather mixed file types
8. Gather deeply nested directory
9. Gather with multiple patterns
10. Gather large file (>1MB)
11. Select with default patterns
12. Select with custom noise patterns
13. Select with capture groups (preserve tail)
14. Select empty content
15. Select with keep_sections (future compat)
16. Select aggressive noise removal
17. Structure spec document
18. Structure archive document
19. Structure handoff document
20. Structure memory document
21. Structure with custom metadata
22. Structure empty sources
23. Compress natural language
24. Compress code block
25. Compress JSON block (minify)
26. Compress stack trace (truncate)
27. Compress aggressive mode
28. Full pipeline: spec type
29. Full pipeline: archive type
30. Full pipeline: handoff type with aggressive compress

### Category 2: Archiving & Context Compression (20 tasks)

31. Archive single file
32. Archive file with topic and summary
33. Archive nonexistent file (error)
34. Archive already archived file
35. Archive updates MEMORY_INDEX.md
36. Compress context file
37. Compress with aggressive flag
38. Compress empty file
39. Compress nonexistent file (error)
40. Compress HTML-heavy content
41. Compress hash-heavy content
42. Compress log file with stack trace
43. Compress JSON document
44. Compress mixed markdown/code
45. Archive and then compress archived doc
46. Compress and then archive compressed doc
47. Archive to custom docs_root
48. MEMORY_INDEX.md append consistency
49. Archive path safety validation
50. Compress path safety validation

### Category 3: A2A Protocol (20 tasks)

51. Write envelope with auto-populated fields
52. Write envelope with explicit message_id
53. Write envelope with all required fields
54. Read envelope for agent "taibai"
55. Read envelope when none exists
56. Read envelope moves file to claimed/
57. Write envelope creates pending/ directory
58. Write envelope filename format validation
59. Read envelope JSON extraction accuracy
60. Write envelope with Unicode content
61. Write envelope with large payload
62. Read envelope after multiple writes (most recent)
63. Write envelope without message_type
64. Write envelope with invalid inbox_dir (error)
65. A2A envelope round-trip (write then read)
66. A2A envelope with document_ref field
67. A2A envelope priority levels
68. A2A envelope handoff type
69. A2A envelope request type
70. A2A envelope response type

### Category 4: Review Request (20 tasks)

71. Request review format type
72. Request review quality type
73. Request review assertion type
74. Request review architecture type
75. Request review generates ticket ID
76. Request review writes A2A envelope
77. Request review envelope has "review-pool" to field
78. Request review with context notes
79. Request review nonexistent document (error)
80. Request review empty document
81. Request review large document
82. Request review document with unverified assertions
83. Request review document with critical risk
84. Request review document with high risk
85. Request review spec document (auto-trigger)
86. Request review archive document (skip)
87. Request review handoff document (auto-trigger)
88. Request review multiple times on same doc
89. Request review ticket uniqueness
90. Request review envelope JSON validity

### Category 5: Integration & End-to-End (10 tasks)

91. E2E: Gather → Select → Structure → Compress → Archive
92. E2E: GSSC pipeline → request_review
93. E2E: GSSC pipeline → write_envelope (handoff)
94. E2E: Read envelope → structure handoff document
95. E2E: Full document lifecycle (gather to archive with review)
96. MCP Server: List all registered tools
97. MCP Server: Call each tool via MCP interface
98. SKILL.md vs MCP Server consistency check
99. Persona vs Tool capability consistency check
100. Full regression: `pytest tests/` with all new tests

### Audit Process

After the 100 tasks, Taibai generates a validation report document. The report is then audited for:
- YAML frontmatter compliance (Pillar 2)
- Fact assertion marking accuracy (Pillar 4.2)
- Risk severity grading correctness (Pillar 4.3)
- GSSC pipeline usage in report generation (Pillar 5)

Issues found during audit feed back into fixes. Iterate until clean.

---

## Success Criteria

1. `skills/tool_taibai/SKILL.md` declares all 7 tools (6 existing + 1 new).
2. `agents/taibai.md` contains explicit GSSC invocation guidance and A2A protocol sections.
3. `agents/taibai.md` contains no hard-coded references to WangLingGuan for review dispatch.
4. `mcp-servers/taibai_server.py` registers all 7 MCP tools.
5. All 100 validation tasks pass.
6. Generated validation report passes format audit.
7. No regressions in existing tests.
