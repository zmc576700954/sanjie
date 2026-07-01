"""DocHub skill wrapper for format generation.

This component exists primarily to drive the agents-develop migration layer
so it can generate Claude SKILL.md, Cursor SKILL.md + cursor_config.json,
ZCode Command.md, and an MCP server entry point for DocHub.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, ComponentType
from core.skills.base import SkillBase


class DochubSkill(SkillBase):
    """Skill definition for DocHub knowledge-base integration."""

    def __init__(self) -> None:
        metadata = ComponentMetadata(
            name="dochub",
            type=ComponentType.SKILL,
            version="1.0.0",
            description="Team knowledge base for managing Markdown documents, contributor addendums, and AI-powered search via MCP.",
            tags=["docs", "knowledge-base", "search", "mcp"],
            supported_tools=["claude", "cursor", "zcode", "mcp"],
        )
        super().__init__(metadata)

    @property
    def instructions(self) -> str:
        return """You are a DocHub knowledge-base assistant.

DocHub stores the team's Markdown technical documents using a "master document + contributor addendum" model:
- A master document is created by one author and can be updated only by that author.
- Other contributors add their changes as "addendums" so nothing is overwritten.
- Documents are classified with Diátaxis types: tutorial, how-to, reference, explanation.

When the user asks about project knowledge, documentation, deployment steps, APIs, conventions, or any team know-how, use the DocHub MCP tools.

Available tools:
- doc_search: keyword/semantic/hybrid search over the knowledge base. Supports filters by author, contributor, session_id, doc_type, and tags.
- doc_query: RAG-style question answering that returns a prompt you can use to answer the user.
- doc_read: read a master document or a contributor addendum.
- doc_create: create a new master document.
- doc_update_master: append an update to an existing master document (author only).
- doc_add_addendum: add or update a contributor addendum for a master document.
- doc_index_status: check indexing status.

Guidelines:
1. Prefer doc_search or doc_query for knowledge questions.
2. When reading, include relevant addendums from contributors.
3. When updating, respect the master/addendum model: original authors update the master; others create addendums.
4. Cite the document title, type, author, and contributor when answering from DocHub.
"""

    def get_checklist(self) -> List[str]:
        return [
            "Identify whether the question needs search or a direct read.",
            "Use doc_search or doc_query with appropriate filters.",
            "Read master documents and relevant addendums.",
            "Synthesize the answer and cite sources.",
        ]

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "DocHub skill loaded. Use the DocHub MCP tools to interact with the knowledge base."}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True
