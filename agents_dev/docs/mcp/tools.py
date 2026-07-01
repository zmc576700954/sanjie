"""DocHub ToolBase implementation exposing all DocHub operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from core.mcp_base.tool_def import MCPToolDefinition
from core.shared.base import ComponentMetadata, ComponentType
from core.tools.base import ToolBase

from agents_dev.docs.chunker import MarkdownChunker
from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.indexer.hybrid import HybridSearcher
from agents_dev.docs.indexer.sqlite_idx import SQLiteFTS5Index
from agents_dev.docs.models import MasterDocument, SearchFilters
from agents_dev.docs.prompts.loader import PromptRenderer
from agents_dev.docs.store import DocumentStore


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


import hashlib
import re


def _to_doc_id(title: str) -> str:
    normalized = re.sub(r"[\s\-]+", "_", title.lower())
    normalized = re.sub(r"[^a-z0-9_\-]", "", normalized)
    normalized = re.sub(r"_{2,}", "_", normalized).strip("_")
    if not normalized:
        return f"doc_{hashlib.md5(title.encode('utf-8')).hexdigest()[:8]}"
    return normalized


class DocHubTool(ToolBase):
    """Tool implementation exposing DocHub operations via MCP."""

    def __init__(self, config: DocHubConfig) -> None:
        metadata = ComponentMetadata(
            name="dochub_tool",
            type=ComponentType.TOOL,
            version="1.0.0",
            description="Tools for managing and searching the DocHub knowledge base.",
            supported_tools=["mcp"],
        )
        super().__init__(metadata)
        self.config = config
        self.store = DocumentStore(config.docs_path)
        self.chunker = MarkdownChunker(
            size=config.chunk_size,
            overlap=config.chunk_overlap,
        )
        keyword_backend = SQLiteFTS5Index(config.index_path / "sqlite_fts5.db")
        self.searcher = HybridSearcher(keyword_backend, rrf_k=config.rrf_k)
        self.renderer = PromptRenderer(config.templates_path)
        self._reindex()

    @property
    def function_definitions(self) -> List[Dict[str, Any]]:
        return [
            MCPToolDefinition(
                name="doc_search",
                description="Search the DocHub knowledge base using keyword, semantic, or hybrid search.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "mode": {"type": "string", "enum": ["keyword", "semantic", "hybrid"], "default": "hybrid"},
                        "filters": {"type": "object", "default": {}},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            ).to_mcp_format(),
            MCPToolDefinition(
                name="doc_query",
                description="Answer a question using RAG over the DocHub knowledge base.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "context_limit": {"type": "integer", "default": 5},
                        "filters": {"type": "object", "default": {}},
                    },
                    "required": ["question"],
                },
            ).to_mcp_format(),
            MCPToolDefinition(
                name="doc_read",
                description="Read a master document or a contributor addendum.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string"},
                        "addendum_id": {"type": "string"},
                    },
                    "required": ["doc_id"],
                },
            ).to_mcp_format(),
            MCPToolDefinition(
                name="doc_create",
                description="Create a new master document in the knowledge base.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "author": {"type": "string"},
                        "doc_type": {"type": "string", "enum": ["tutorial", "how-to", "reference", "explanation"]},
                        "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                        "session_id": {"type": "string"},
                        "summary": {"type": "string"},
                    },
                    "required": ["title", "content", "author", "doc_type"],
                },
            ).to_mcp_format(),
            MCPToolDefinition(
                name="doc_update_master",
                description="Append an update to an existing master document (author only).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string"},
                        "content_delta": {"type": "string"},
                        "summary": {"type": "string"},
                    },
                    "required": ["doc_id", "content_delta"],
                },
            ).to_mcp_format(),
            MCPToolDefinition(
                name="doc_add_addendum",
                description="Add or update a contributor addendum for a master document.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_doc_id": {"type": "string"},
                        "contributor": {"type": "string"},
                        "content": {"type": "string"},
                        "summary": {"type": "string"},
                    },
                    "required": ["parent_doc_id", "contributor", "content"],
                },
            ).to_mcp_format(),
            MCPToolDefinition(
                name="doc_index_status",
                description="Check the indexing status of the knowledge base or a specific document.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string"},
                    },
                },
            ).to_mcp_format(),
        ]

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that input_data meets the component's requirements."""
        return isinstance(input_data, dict) and "function" in input_data

    def run(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        handlers = {
            "doc_search": self._doc_search,
            "doc_query": self._doc_query,
            "doc_read": self._doc_read,
            "doc_create": self._doc_create,
            "doc_update_master": self._doc_update_master,
            "doc_add_addendum": self._doc_add_addendum,
            "doc_index_status": self._doc_index_status,
        }
        handler = handlers.get(function_name)
        if handler is None:
            raise ValueError(f"Unknown function: {function_name}")
        return handler(arguments)

    def _doc_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        filters = SearchFilters(**args.get("filters", {}))
        filters.limit = args.get("limit", filters.limit)
        result = self.searcher.search(
            query=args["query"],
            mode=args.get("mode", self.config.default_search_mode),
            filters=filters,
        )
        return {
            "chunks": [c.model_dump(mode="json") for c in result.chunks],
            "total": result.total,
            "query": result.query,
            "mode": result.mode,
        }

    def _doc_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        filters = SearchFilters(**args.get("filters", {}))
        filters.limit = args.get("context_limit", filters.limit)
        result = self.searcher.search(
            query=args["question"],
            mode="hybrid",
            filters=filters,
        )
        prompt = self.renderer.render(
            "rag_answer",
            query=args["question"],
            chunks=result.chunks,
        )
        return {
            "prompt": prompt,
            "chunks_used": len(result.chunks),
            "query": args["question"],
        }

    def _doc_read(self, args: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = args["doc_id"]
        addendum_id = args.get("addendum_id")
        master = self.store.get_master(doc_id)
        content = self.store.read_content(master.content_path)
        if addendum_id:
            contributor = addendum_id.split(".")[-1]
            addendum = master.addendums.get(contributor)
            if addendum is None:
                from agents_dev.docs.errors import AddendumNotFoundError
                raise AddendumNotFoundError(f"Addendum '{addendum_id}' not found")
            return {
                "doc_id": doc_id,
                "addendum_id": addendum_id,
                "content": self.store.read_content(addendum.content_path),
                "metadata": addendum.model_dump(mode="json"),
            }
        return {
            "doc_id": doc_id,
            "content": content,
            "metadata": master.model_dump(mode="json"),
            "addendums": list(master.addendums.keys()),
        }

    def _doc_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = _to_doc_id(args["title"])
        now = _utc_now()
        content_path = self.store.master_dir / f"{doc_id}.md"
        master = MasterDocument(
            doc_id=doc_id,
            title=args["title"],
            author=args["author"],
            doc_type=args["doc_type"],
            session_id=args.get("session_id"),
            tags=args.get("tags", []),
            summary=args.get("summary"),
            created_at=now,
            updated_at=now,
            content_path=content_path,
        )
        self.store.create_master(master, args["content"])
        self._reindex()
        return {"doc_id": doc_id, "status": "created"}

    def _doc_update_master(self, args: Dict[str, Any]) -> Dict[str, Any]:
        master = self.store.update_master(
            args["doc_id"],
            args["content_delta"],
            args.get("summary", "update"),
        )
        self._reindex()
        return {"doc_id": master.doc_id, "status": "updated"}

    def _doc_add_addendum(self, args: Dict[str, Any]) -> Dict[str, Any]:
        addendum = self.store.create_or_update_addendum(
            args["parent_doc_id"],
            args["contributor"],
            args["content"],
            args.get("summary", ""),
        )
        self._reindex()
        return {
            "addendum_id": addendum.addendum_id,
            "status": "created_or_updated",
        }

    def _doc_index_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = args.get("doc_id")
        masters = self.store.list_masters()
        return {
            "total_documents": len(masters),
            "doc_id": doc_id,
            "indexed": doc_id is not None and any(m.doc_id == doc_id for m in masters),
        }

    def _reindex(self) -> None:
        self.searcher.clear()
        chunks: List[Any] = []
        for master in self.store.list_masters():
            chunks.extend(self.chunker.chunk_document(master, self.store.read_content))
            for addendum in master.addendums.values():
                chunks.extend(self.chunker.chunk_addendum(addendum, master, self.store.read_content))
        self.searcher.index_chunks(chunks)
