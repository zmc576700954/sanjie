# DocHub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement DocHub, a team knowledge-base plugin for `agents-develop` that manages Markdown documents with a master-document + contributor-addendum model, hybrid search, MCP server exposure, dynamic Jinja2 prompts, and AI skill-file generation.

**Architecture:** DocHub is built as a core Python package (`agents_dev/docs/`) with a local filesystem store, pluggable index backends (SQLite FTS5 baseline with optional Meilisearch/ChromaDB), and an MCP server that registers ToolBase instances. CLI commands are added under `agents-dev docs`, and format files are generated via the existing migration layer.

**Tech Stack:** Python >=3.10, Pydantic, Jinja2, Click, Rich, markdown, python-frontmatter, SQLite FTS5. Optional: meilisearch-python, chromadb, sentence-transformers.

## Global Constraints

- Python version floor: `>=3.10`
- Line length: 100 (ruff config)
- Every new file must include a module docstring.
- All core classes that are components must inherit from `CoreComponent` or project base classes.
- All custom errors must inherit from `AgentsDevelopError`.
- All CLI commands must use Click and the project `Console` pattern.
- Tests must use pytest and live under `tests/`.
- Each task must end with passing tests and a git commit.

---

## File Map

This plan creates the following files:

| File | Responsibility |
|---|---|
| `agents_dev/docs/__init__.py` | Package init, exposes public API where appropriate |
| `agents_dev/docs/errors.py` | DocHub-specific error classes |
| `agents_dev/docs/models.py` | Pydantic models: `MasterDocument`, `Addendum`, `DocChunk`, `SearchFilters`, `SearchResult` |
| `agents_dev/docs/config.py` | `DocHubConfig` -- loads `dochub.yaml` |
| `agents_dev/docs/store.py` | `DocumentStore` -- local filesystem CRUD and metadata management |
| `agents_dev/docs/parser/markdown_parser.py` | Parse Markdown + YAML frontmatter |
| `agents_dev/docs/chunker.py` | `MarkdownChunker` -- split documents into chunks with heading paths |
| `agents_dev/docs/indexer/base.py` | `IndexBackend` ABC |
| `agents_dev/docs/indexer/sqlite_idx.py` | `SQLiteFTS5Index` -- baseline keyword index |
| `agents_dev/docs/indexer/hybrid.py` | `HybridSearcher` -- dispatches to backends, filters, RRF |
| `agents_dev/docs/prompts/loader.py` | `PromptRenderer` -- Jinja2 template loader |
| `agents_dev/docs/prompts/templates/search_context.j2` | Default search-context prompt template |
| `agents_dev/docs/prompts/templates/rag_answer.j2` | Default RAG answer prompt template |
| `agents_dev/docs/mcp/tools.py` | `DocHubTool` -- ToolBase implementation exposing all DocHub functions |
| `agents_dev/docs/mcp/server.py` | `DocHubMCPServer` -- MCPServerBase subclass |
| `cli/docs_cmd.py` | Click group and subcommands for `agents-dev docs` |
| `cli/main.py` | Modified to register `docs_cmd` |
| `tests/docs/test_models.py` | Model validation tests |
| `tests/docs/test_store.py` | DocumentStore tests |
| `tests/docs/test_chunker.py` | Markdown chunker tests |
| `tests/docs/test_sqlite_index.py` | SQLite FTS5 index tests |
| `tests/docs/test_hybrid_searcher.py` | HybridSearcher / filter tests |
| `tests/docs/test_prompt_renderer.py` | Jinja2 template tests |
| `tests/docs/test_mcp_tools.py` | DocHubTool / server tests |
| `tests/docs/test_cli.py` | CLI tests using Click's `CliRunner` |

---

## Task 1: DocHub Errors, Models, and Config

**Files:**
- Create: `agents_dev/docs/errors.py`
- Create: `agents_dev/docs/models.py`
- Create: `agents_dev/docs/config.py`
- Create: `agents_dev/docs/__init__.py`
- Create: `tests/docs/test_models.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `DocHubError`, `DocumentNotFoundError`, `DuplicateDocumentError`, `InvalidDocumentTypeError`
- Produces: `MasterDocument`, `Addendum`, `DocChunk`, `SearchFilters`, `SearchResult`
- Produces: `DocHubConfig` with `from_yaml(path: Path) -> DocHubConfig`

- [ ] **Step 1: Add DocHub dependencies to `pyproject.toml`**

Add under `[project.dependencies]`:

```toml
dependencies = [
    "jinja2>=3.1",
    "jsonschema>=4.0",
    "pydantic>=2.0",
    "rich>=13.0",
    "click>=8.0",
    "markdown>=3.5",
    "python-frontmatter>=1.0",
]
```

- [ ] **Step 2: Write the failing model tests**

Create `tests/docs/test_models.py`:

```python
"""Tests for DocHub data models."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.models import (
    Addendum,
    DocChunk,
    MasterDocument,
    SearchFilters,
    SearchResult,
)


def test_master_document_requires_valid_doc_type():
    with pytest.raises(ValueError):
        MasterDocument(
            doc_id="bad_type",
            title="Bad Type",
            author="alice",
            doc_type="essay",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            content_path=Path("docs/master/bad_type.md"),
        )


def test_addendum_parent_doc_id_matches_doc_id():
    addendum = Addendum(
        addendum_id="api_deploy.bob",
        parent_doc_id="api_deploy",
        contributor="bob",
        summary="Docker deploy notes",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("docs/addendums/api_deploy.bob.md"),
    )
    assert addendum.addendum_id == "api_deploy.bob"


def test_doc_chunk_has_required_metadata():
    chunk = DocChunk(
        chunk_id="api_deploy_0",
        doc_id="api_deploy",
        doc_title="API Deploy",
        doc_type="how-to",
        author="alice",
        contributor=None,
        session_id="sess_001",
        tags=["api"],
        heading_path=["API Deploy"],
        content="Run pytest first.",
        source_path=Path("docs/master/api_deploy.md"),
    )
    assert chunk.contributor is None


def test_search_filters_defaults():
    filters = SearchFilters()
    assert filters.author is None
    assert filters.limit == 10


def test_search_result_ranking():
    result = SearchResult(
        chunks=[],
        total=0,
        query="deploy",
        mode="hybrid",
    )
    assert result.mode == "hybrid"
```

- [ ] **Step 3: Run model tests to verify they fail**

Run:

```bash
pytest tests/docs/test_models.py -v
```

Expected: failures because modules do not exist.

- [ ] **Step 4: Implement errors, models, and config**

Create `agents_dev/docs/errors.py`:

```python
"""DocHub-specific errors."""

from __future__ import annotations

from core.shared.errors import ComponentError


class DocHubError(ComponentError):
    """Base error for DocHub operations."""


class DocumentNotFoundError(DocHubError):
    """Raised when a requested document is not found."""


class AddendumNotFoundError(DocHubError):
    """Raised when a requested addendum is not found."""


class DuplicateDocumentError(DocHubError):
    """Raised when creating a document with an existing doc_id."""


class InvalidDocumentTypeError(DocHubError):
    """Raised when a document type is not a valid Diátaxis type."""
```

Create `agents_dev/docs/models.py`:

```python
"""Pydantic models for DocHub documents, chunks, and search."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from agents_dev.docs.errors import InvalidDocumentTypeError

VALID_DOC_TYPES = {"tutorial", "how-to", "reference", "explanation"}
VALID_SEARCH_MODES = {"keyword", "semantic", "hybrid"}


class Addendum(BaseModel):
    """A contributor addendum linked to a master document."""

    addendum_id: str
    parent_doc_id: str
    contributor: str
    summary: str
    created_at: datetime
    updated_at: datetime
    content_path: Path
    versions: List[str] = Field(default_factory=list)


class MasterDocument(BaseModel):
    """A master document in the DocHub knowledge base."""

    doc_id: str
    title: str
    author: str
    doc_type: str
    session_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    content_path: Path
    addendums: Dict[str, Addendum] = Field(default_factory=dict)

    @field_validator("doc_type")
    @classmethod
    def _validate_doc_type(cls, value: str) -> str:
        if value not in VALID_DOC_TYPES:
            raise InvalidDocumentTypeError(
                f"Invalid doc_type '{value}'. Must be one of {sorted(VALID_DOC_TYPES)}"
            )
        return value


class DocChunk(BaseModel):
    """A searchable chunk of a document."""

    chunk_id: str
    doc_id: str
    doc_title: str
    doc_type: str
    author: str
    contributor: Optional[str]
    session_id: Optional[str]
    tags: List[str]
    heading_path: List[str]
    content: str
    source_path: Path


class SearchFilters(BaseModel):
    """Filters applied to a DocHub search."""

    author: Optional[str] = None
    contributor: Optional[str] = None
    session_id: Optional[str] = None
    doc_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    limit: int = 10


class SearchResult(BaseModel):
    """Result of a DocHub search."""

    chunks: List[DocChunk]
    total: int
    query: str
    mode: str
```

Create `agents_dev/docs/config.py`:

```python
"""DocHub configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class DocHubConfig:
    """Runtime configuration for a DocHub knowledge base."""

    def __init__(self, data: Dict[str, Any], base_path: Path) -> None:
        self._data = data
        self.base_path = base_path

    @classmethod
    def from_yaml(cls, path: Path) -> "DocHubConfig":
        """Load configuration from a dochub.yaml file."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls(data, base_path=path.parent)

    @property
    def name(self) -> str:
        return self._data.get("name", "dochub")

    @property
    def docs_path(self) -> Path:
        return self.base_path / "docs"

    @property
    def index_path(self) -> Path:
        return self.base_path / "index"

    @property
    def templates_path(self) -> Path:
        return Path(__file__).parent / "prompts" / "templates"

    @property
    def keyword_backend(self) -> str:
        return self._data.get("index", {}).get("keyword", {}).get("backend", "sqlite")

    @property
    def vector_backend(self) -> Optional[str]:
        return self._data.get("index", {}).get("vector", {}).get("backend")

    @property
    def chunk_size(self) -> int:
        return self._data.get("chunking", {}).get("size", 512)

    @property
    def chunk_overlap(self) -> int:
        return self._data.get("chunking", {}).get("overlap", 100)

    @property
    def default_search_mode(self) -> str:
        return self._data.get("search", {}).get("default_mode", "keyword")

    @property
    def top_k(self) -> int:
        return self._data.get("search", {}).get("top_k", 10)

    @property
    def rrf_k(self) -> int:
        return self._data.get("search", {}).get("rrf_k", 60)
```

Create `agents_dev/docs/__init__.py`:

```python
"""DocHub team knowledge-base plugin."""

from __future__ import annotations

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.models import Addendum, DocChunk, MasterDocument

__all__ = ["DocHubConfig", "Addendum", "DocChunk", "MasterDocument"]
```

- [ ] **Step 5: Run model tests to verify they pass**

Run:

```bash
pytest tests/docs/test_models.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml agents_dev/docs tests/docs
git commit -m "feat(docs): add DocHub errors, models, and config

- DocHub-specific error hierarchy
- Pydantic models for MasterDocument, Addendum, DocChunk, SearchFilters, SearchResult
- DocHubConfig loader for dochub.yaml

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Markdown Parser and Document Store

**Files:**
- Create: `agents_dev/docs/parser/__init__.py`
- Create: `agents_dev/docs/parser/markdown_parser.py`
- Create: `agents_dev/docs/store.py`
- Create: `tests/docs/test_store.py`
- Create: `tests/docs/test_markdown_parser.py`

**Interfaces:**
- Consumes: `MasterDocument`, `Addendum`, DocHub errors
- Produces: `parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]`
- Produces: `DocumentStore` with methods:
  - `create_master(master: MasterDocument, content: str) -> MasterDocument`
  - `get_master(doc_id: str) -> MasterDocument`
  - `update_master(doc_id: str, content_delta: str, summary: str) -> MasterDocument`
  - `create_or_update_addendum(doc_id: str, contributor: str, content: str, summary: str) -> Addendum`
  - `read_content(path: Path) -> str`
  - `list_masters(filters: Optional[Dict[str, Any]] = None) -> List[MasterDocument]`

- [ ] **Step 1: Write failing parser and store tests**

Create `tests/docs/test_markdown_parser.py`:

```python
"""Tests for Markdown parsing utilities."""

from agents_dev.docs.parser.markdown_parser import parse_frontmatter


def test_parse_frontmatter_extracts_metadata():
    text = """---
title: API Deploy
author: alice
doc_type: how-to
tags: [api, deploy]
---
Run pytest.
"""
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "API Deploy"
    assert meta["author"] == "alice"
    assert "Run pytest" in body


def test_parse_frontmatter_without_frontmatter():
    meta, body = parse_frontmatter("Plain content.")
    assert meta == {}
    assert body == "Plain content."
```

Create `tests/docs/test_store.py`:

```python
"""Tests for DocumentStore."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.models import MasterDocument
from agents_dev.docs.store import DocumentStore


@pytest.fixture
def tmp_store(tmp_path):
    store = DocumentStore(tmp_path / "docs")
    return store


def test_create_and_get_master(tmp_store):
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        tags=["api"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=tmp_store.docs_path / "master" / "api_deploy.md",
    )
    created = tmp_store.create_master(master, "Run pytest.")
    assert created.doc_id == "api_deploy"

    fetched = tmp_store.get_master("api_deploy")
    assert fetched.title == "API Deploy"
    assert tmp_store.read_content(fetched.content_path) == "Run pytest."


def test_update_master_appends_delta(tmp_store):
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=tmp_store.docs_path / "master" / "api_deploy.md",
    )
    tmp_store.create_master(master, "Run pytest.")
    updated = tmp_store.update_master("api_deploy", "Then deploy.", "add deploy step")
    assert "Run pytest." in tmp_store.read_content(updated.content_path)
    assert "Then deploy." in tmp_store.read_content(updated.content_path)


def test_create_addendum(tmp_store):
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=tmp_store.docs_path / "master" / "api_deploy.md",
    )
    tmp_store.create_master(master, "Run pytest.")
    addendum = tmp_store.create_or_update_addendum(
        "api_deploy", "bob", "Docker deploy notes.", "Docker notes"
    )
    assert addendum.contributor == "bob"
    assert "Docker deploy notes" in tmp_store.read_content(addendum.content_path)

    master_after = tmp_store.get_master("api_deploy")
    assert "bob" in master_after.addendums
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/docs/test_markdown_parser.py tests/docs/test_store.py -v
```

Expected: failures because modules do not exist.

- [ ] **Step 3: Implement parser and store**

Create `agents_dev/docs/parser/__init__.py`:

```python
"""DocHub document parsers."""

from __future__ import annotations
```

Create `agents_dev/docs/parser/markdown_parser.py`:

```python
"""Markdown and frontmatter parsing utilities."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import frontmatter


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter and return metadata + body.

    Args:
        content: Raw Markdown content, optionally with YAML frontmatter.

    Returns:
        Tuple of (metadata dict, markdown body string).
    """
    post = frontmatter.loads(content)
    return dict(post.metadata), post.content


def dump_frontmatter(metadata: Dict[str, Any], content: str) -> str:
    """Serialize metadata and body to a Markdown string with YAML frontmatter."""
    post = frontmatter.Post(content, **metadata)
    return frontmatter.dumps(post)
```

Create `agents_dev/docs/store.py`:

```python
"""Local filesystem storage for DocHub documents."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents_dev.docs.errors import (
    AddendumNotFoundError,
    DocumentNotFoundError,
    DuplicateDocumentError,
)
from agents_dev.docs.models import Addendum, MasterDocument
from agents_dev.docs.parser.markdown_parser import dump_frontmatter


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStore:
    """Manages master documents and contributor addendums on the local filesystem."""

    def __init__(self, docs_path: Path) -> None:
        self.docs_path = Path(docs_path)
        self.master_dir = self.docs_path / "master"
        self.addendum_dir = self.docs_path / "addendums"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.master_dir.mkdir(parents=True, exist_ok=True)
        self.addendum_dir.mkdir(parents=True, exist_ok=True)

    def create_master(self, master: MasterDocument, content: str) -> MasterDocument:
        """Create a new master document on disk."""
        if master.content_path.exists() or self._meta_path(master.doc_id).exists():
            raise DuplicateDocumentError(f"Document '{master.doc_id}' already exists")

        self.master_dir.mkdir(parents=True, exist_ok=True)
        metadata = self._master_to_metadata(master)
        content_with_frontmatter = dump_frontmatter(metadata, content)
        master.content_path.write_text(content_with_frontmatter, encoding="utf-8")
        self._write_meta(master.doc_id, metadata)
        return master

    def get_master(self, doc_id: str) -> MasterDocument:
        """Load a master document by doc_id."""
        meta = self._read_meta(doc_id)
        content_path = self.master_dir / f"{doc_id}.md"
        if not content_path.exists():
            raise DocumentNotFoundError(f"Document '{doc_id}' not found")
        return self._metadata_to_master(meta, content_path)

    def update_master(self, doc_id: str, content_delta: str, summary: str) -> MasterDocument:
        """Append a content delta to the master document."""
        master = self.get_master(doc_id)
        existing = self.read_content(master.content_path)
        timestamp = _utc_now().isoformat()
        update_block = f"\n\n---update---\n# update: {summary}\n# time: {timestamp}\n\n{content_delta}"
        new_content = existing + update_block
        master.content_path.write_text(new_content, encoding="utf-8")
        master.updated_at = _utc_now()
        master.summary = summary
        self._write_meta(master.doc_id, self._master_to_metadata(master))
        return master

    def create_or_update_addendum(
        self,
        doc_id: str,
        contributor: str,
        content: str,
        summary: str,
    ) -> Addendum:
        """Create or update a contributor addendum for a master document."""
        master = self.get_master(doc_id)
        addendum_id = f"{doc_id}.{contributor}"
        content_path = self.addendum_dir / f"{addendum_id}.md"
        now = _utc_now()

        if content_path.exists():
            existing_versions = master.addendums.get(contributor, Addendum(
                addendum_id=addendum_id,
                parent_doc_id=doc_id,
                contributor=contributor,
                summary="",
                created_at=now,
                updated_at=now,
                content_path=content_path,
            )).versions or []
            snapshot_name = f"{addendum_id}.v{len(existing_versions) + 1}.md"
            old_snapshot = self.addendum_dir / snapshot_name
            shutil.copy2(content_path, old_snapshot)
            existing_versions.append(old_snapshot.name)
            created_at = master.addendums[contributor].created_at
        else:
            existing_versions = []
            created_at = now

        addendum = Addendum(
            addendum_id=addendum_id,
            parent_doc_id=doc_id,
            contributor=contributor,
            summary=summary,
            created_at=created_at,
            updated_at=now,
            content_path=content_path,
            versions=existing_versions,
        )

        metadata = self._addendum_to_metadata(addendum)
        content_with_frontmatter = dump_frontmatter(metadata, content)
        content_path.write_text(content_with_frontmatter, encoding="utf-8")

        master.addendums[contributor] = addendum
        self._write_meta(master.doc_id, self._master_to_metadata(master))
        return addendum

    def read_content(self, path: Path) -> str:
        """Read Markdown content, stripping frontmatter."""
        from agents_dev.docs.parser.markdown_parser import parse_frontmatter

        _, body = parse_frontmatter(Path(path).read_text(encoding="utf-8"))
        return body

    def list_masters(self, filters: Optional[Dict[str, Any]] = None) -> List[MasterDocument]:
        """List master documents, optionally filtered by metadata."""
        filters = filters or {}
        masters: List[MasterDocument] = []
        for meta_path in sorted(self.master_dir.glob("*.meta.json")):
            doc_id = meta_path.stem.replace(".meta", "")
            master = self.get_master(doc_id)
            if all(
                getattr(master, key, None) == value or (key == "tag" and value in master.tags)
                for key, value in filters.items()
            ):
                masters.append(master)
        return masters

    def _meta_path(self, doc_id: str) -> Path:
        return self.master_dir / f"{doc_id}.meta.json"

    def _read_meta(self, doc_id: str) -> Dict[str, Any]:
        path = self._meta_path(doc_id)
        if not path.exists():
            raise DocumentNotFoundError(f"Document '{doc_id}' not found")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write_meta(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        path = self._meta_path(doc_id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def _master_to_metadata(master: MasterDocument) -> Dict[str, Any]:
        return {
            "doc_id": master.doc_id,
            "title": master.title,
            "author": master.author,
            "doc_type": master.doc_type,
            "session_id": master.session_id,
            "tags": master.tags,
            "summary": master.summary,
            "created_at": master.created_at.isoformat(),
            "updated_at": master.updated_at.isoformat(),
            "addendums": {
                contributor: {
                    "contributor": a.contributor,
                    "summary": a.summary,
                    "created_at": a.created_at.isoformat(),
                    "updated_at": a.updated_at.isoformat(),
                    "versions": a.versions,
                }
                for contributor, a in master.addendums.items()
            },
        }

    @staticmethod
    def _metadata_to_master(data: Dict[str, Any], content_path: Path) -> MasterDocument:
        addendums = {
            contributor: Addendum(
                addendum_id=f"{data['doc_id']}.{contributor}",
                parent_doc_id=data["doc_id"],
                contributor=contributor,
                summary=a["summary"],
                created_at=datetime.fromisoformat(a["created_at"]),
                updated_at=datetime.fromisoformat(a["updated_at"]),
                content_path=content_path.parent.parent / "addendums" / f"{data['doc_id']}.{contributor}.md",
                versions=a.get("versions", []),
            )
            for contributor, a in data.get("addendums", {}).items()
        }
        return MasterDocument(
            doc_id=data["doc_id"],
            title=data["title"],
            author=data["author"],
            doc_type=data["doc_type"],
            session_id=data.get("session_id"),
            tags=data.get("tags", []),
            summary=data.get("summary"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            content_path=content_path,
            addendums=addendums,
        )

    @staticmethod
    def _addendum_to_metadata(addendum: Addendum) -> Dict[str, Any]:
        return {
            "addendum_id": addendum.addendum_id,
            "parent_doc_id": addendum.parent_doc_id,
            "contributor": addendum.contributor,
            "summary": addendum.summary,
            "created_at": addendum.created_at.isoformat(),
            "updated_at": addendum.updated_at.isoformat(),
            "versions": addendum.versions,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_markdown_parser.py tests/docs/test_store.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents_dev/docs/parser tests/docs
git commit -m "feat(docs): add DocumentStore and Markdown parser

- parse YAML frontmatter from Markdown documents
- create/read/update master documents
- create/update contributor addendums with version snapshots

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Markdown Chunker

**Files:**
- Create: `agents_dev/docs/chunker.py`
- Create: `tests/docs/test_chunker.py`

**Interfaces:**
- Consumes: `MasterDocument`, `Addendum`
- Produces: `MarkdownChunker` with method `chunk_document(master: MasterDocument, read_content: Callable[[Path], str]) -> List[DocChunk]` and `chunk_addendum(addendum: Addendum, master: MasterDocument, read_content: Callable[[Path], str]) -> List[DocChunk]`

- [ ] **Step 1: Write failing chunker tests**

Create `tests/docs/test_chunker.py`:

```python
"""Tests for MarkdownChunker."""

from datetime import datetime
from pathlib import Path

from agents_dev.docs.chunker import MarkdownChunker
from agents_dev.docs.models import MasterDocument


def test_chunker_splits_by_headings():
    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("api_deploy.md"),
    )
    content = """# API Deploy

Run pytest.

## Docker

Use docker build.

## Kubernetes

Use kubectl apply.
"""
    chunker = MarkdownChunker(size=200, overlap=0)
    chunks = chunker.chunk_document(master, lambda _: content)
    assert len(chunks) >= 2
    assert chunks[0].heading_path == ["API Deploy"]
    assert any("Docker" in c.heading_path for c in chunks)
    assert all(c.doc_id == "api_deploy" for c in chunks)


def test_chunker_addendum_is_single_chunk():
    from agents_dev.docs.models import Addendum

    master = MasterDocument(
        doc_id="api_deploy",
        title="API Deploy",
        author="alice",
        doc_type="how-to",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("api_deploy.md"),
    )
    addendum = Addendum(
        addendum_id="api_deploy.bob",
        parent_doc_id="api_deploy",
        contributor="bob",
        summary="Docker notes",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        content_path=Path("api_deploy.bob.md"),
    )
    chunker = MarkdownChunker(size=512, overlap=0)
    chunks = chunker.chunk_addendum(addendum, master, lambda _: "Docker deploy notes.")
    assert len(chunks) == 1
    assert chunks[0].contributor == "bob"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/docs/test_chunker.py -v
```

Expected: failure because module does not exist.

- [ ] **Step 3: Implement MarkdownChunker**

Create `agents_dev/docs/chunker.py`:

```python
"""Document chunking for DocHub search indexes."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Callable, List

from agents_dev.docs.models import Addendum, DocChunk, MasterDocument


class MarkdownChunker:
    """Split Markdown documents into searchable chunks by heading structure."""

    def __init__(self, size: int = 512, overlap: int = 100) -> None:
        self.size = size
        self.overlap = overlap

    def chunk_document(
        self,
        master: MasterDocument,
        read_content: Callable[[Path], str],
    ) -> List[DocChunk]:
        """Chunk a master document by its heading hierarchy."""
        content = read_content(master.content_path)
        sections = self._split_by_headings(content)
        chunks: List[DocChunk] = []
        for heading_path, section_text in sections:
            chunk_id = f"{master.doc_id}_{uuid.uuid4().hex[:8]}"
            chunks.append(
                DocChunk(
                    chunk_id=chunk_id,
                    doc_id=master.doc_id,
                    doc_title=master.title,
                    doc_type=master.doc_type,
                    author=master.author,
                    contributor=None,
                    session_id=master.session_id,
                    tags=master.tags,
                    heading_path=heading_path,
                    content=section_text.strip(),
                    source_path=master.content_path,
                )
            )
        return chunks

    def chunk_addendum(
        self,
        addendum: Addendum,
        master: MasterDocument,
        read_content: Callable[[Path], str],
    ) -> List[DocChunk]:
        """Chunk an addendum as a single contributor chunk."""
        content = read_content(addendum.content_path)
        return [
            DocChunk(
                chunk_id=f"{addendum.addendum_id}_{uuid.uuid4().hex[:8]}",
                doc_id=master.doc_id,
                doc_title=master.title,
                doc_type=master.doc_type,
                author=master.author,
                contributor=addendum.contributor,
                session_id=master.session_id,
                tags=master.tags,
                heading_path=[addendum.summary],
                content=content.strip(),
                source_path=addendum.content_path,
            )
        ]

    def _split_by_headings(self, content: str) -> List[tuple[List[str], str]]:
        """Split Markdown into (heading_path, section_text) pairs."""
        lines = content.splitlines()
        sections: List[tuple[List[str], str]] = []
        current_path: List[str] = []
        current_lines: List[str] = []

        def flush() -> None:
            if current_lines:
                sections.append((list(current_path), "\n".join(current_lines)))
                current_lines.clear()

        for line in lines:
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                flush()
                level = len(match.group(1))
                title = match.group(2).strip()
                current_path = current_path[: level - 1]
                current_path.append(title)
            else:
                current_lines.append(line)
        flush()

        if not sections:
            sections.append(([], content))

        return sections
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_chunker.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents_dev/docs/chunker.py tests/docs/test_chunker.py
git commit -m "feat(docs): add MarkdownChunker

- split master documents by heading hierarchy
- treat each addendum as a single contributor chunk
- preserve doc metadata on every chunk

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: SQLite FTS5 Keyword Index

**Files:**
- Create: `agents_dev/docs/indexer/__init__.py`
- Create: `agents_dev/docs/indexer/base.py`
- Create: `agents_dev/docs/indexer/sqlite_idx.py`
- Create: `tests/docs/test_sqlite_index.py`

**Interfaces:**
- Produces: `IndexBackend` ABC with `index_chunks(chunks: List[DocChunk]) -> None`, `search(query: str, filters: SearchFilters) -> List[DocChunk]`, `clear() -> None`
- Produces: `SQLiteFTS5Index` implementing `IndexBackend`

- [ ] **Step 1: Write failing SQLite index tests**

Create `tests/docs/test_sqlite_index.py`:

```python
"""Tests for SQLite FTS5 keyword index."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.indexer.sqlite_idx import SQLiteFTS5Index
from agents_dev.docs.models import DocChunk, SearchFilters


@pytest.fixture
def idx(tmp_path):
    return SQLiteFTS5Index(tmp_path / "index.db")


def _chunk(doc_id: str, content: str, contributor=None) -> DocChunk:
    return DocChunk(
        chunk_id=f"{doc_id}_1",
        doc_id=doc_id,
        doc_title="Title",
        doc_type="how-to",
        author="alice",
        contributor=contributor,
        session_id="s1",
        tags=["api"],
        heading_path=["Title"],
        content=content,
        source_path=Path(f"{doc_id}.md"),
    )


def test_index_and_search(idx):
    idx.index_chunks([_chunk("d1", "deploy to production")])
    results = idx.search("deploy", SearchFilters())
    assert len(results) == 1
    assert results[0].doc_id == "d1"


def test_search_filters_by_author(idx):
    idx.index_chunks([
        _chunk("d1", "deploy", contributor=None),
        _chunk("d2", "deploy", contributor="bob"),
    ])
    results = idx.search("deploy", SearchFilters(contributor="bob"))
    assert len(results) == 1
    assert results[0].doc_id == "d2"


def test_clear_index(idx):
    idx.index_chunks([_chunk("d1", "deploy")])
    idx.clear()
    results = idx.search("deploy", SearchFilters())
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/docs/test_sqlite_index.py -v
```

Expected: failures because module does not exist.

- [ ] **Step 3: Implement index backend and SQLite index**

Create `agents_dev/docs/indexer/__init__.py`:

```python
"""DocHub search index backends."""

from __future__ import annotations
```

Create `agents_dev/docs/indexer/base.py`:

```python
"""Abstract base class for DocHub index backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from agents_dev.docs.models import DocChunk, SearchFilters


class IndexBackend(ABC):
    """Abstract index backend for keyword or semantic search."""

    @abstractmethod
    def index_chunks(self, chunks: List[DocChunk]) -> None:
        """Index a list of document chunks."""

    @abstractmethod
    def search(self, query: str, filters: SearchFilters) -> List[DocChunk]:
        """Search the index and return matching chunks."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed chunks."""
```

Create `agents_dev/docs/indexer/sqlite_idx.py`:

```python
"""SQLite FTS5 keyword index backend for DocHub."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List

from agents_dev.docs.indexer.base import IndexBackend
from agents_dev.docs.models import DocChunk, SearchFilters


class SQLiteFTS5Index(IndexBackend):
    """Keyword search using SQLite FTS5."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(content, metadata)")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_meta (
                    chunk_id TEXT PRIMARY KEY,
                    doc_id TEXT,
                    doc_title TEXT,
                    doc_type TEXT,
                    author TEXT,
                    contributor TEXT,
                    session_id TEXT,
                    tags TEXT,
                    heading_path TEXT,
                    source_path TEXT
                )
            """)

    def index_chunks(self, chunks: List[DocChunk]) -> None:
        with self._connection() as conn:
            for chunk in chunks:
                metadata = {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "doc_title": chunk.doc_title,
                    "doc_type": chunk.doc_type,
                    "author": chunk.author,
                    "contributor": chunk.contributor,
                    "session_id": chunk.session_id,
                    "tags": chunk.tags,
                    "heading_path": chunk.heading_path,
                    "source_path": str(chunk.source_path),
                }
                conn.execute(
                    "INSERT OR REPLACE INTO chunks (content, metadata) VALUES (?, ?)",
                    (chunk.content, json.dumps(metadata)),
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunk_meta (
                        chunk_id, doc_id, doc_title, doc_type, author, contributor,
                        session_id, tags, heading_path, source_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.chunk_id,
                        chunk.doc_id,
                        chunk.doc_title,
                        chunk.doc_type,
                        chunk.author,
                        chunk.contributor,
                        chunk.session_id,
                        json.dumps(chunk.tags),
                        json.dumps(chunk.heading_path),
                        str(chunk.source_path),
                    ),
                )
            conn.commit()

    def search(self, query: str, filters: SearchFilters) -> List[DocChunk]:
        sql = "SELECT metadata FROM chunks WHERE content MATCH ?"
        params: List[str] = [query]
        with self._connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        chunks: List[DocChunk] = []
        for row in rows:
            metadata = json.loads(row["metadata"])
            chunk = self._row_to_chunk(metadata)
            if self._matches_filters(chunk, filters):
                chunks.append(chunk)
        return chunks[: filters.limit]

    def clear(self) -> None:
        with self._connection() as conn:
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM chunk_meta")
            conn.commit()

    @staticmethod
    def _row_to_chunk(metadata: dict) -> DocChunk:
        return DocChunk(
            chunk_id=metadata["chunk_id"],
            doc_id=metadata["doc_id"],
            doc_title=metadata["doc_title"],
            doc_type=metadata["doc_type"],
            author=metadata["author"],
            contributor=metadata.get("contributor"),
            session_id=metadata.get("session_id"),
            tags=metadata.get("tags", []),
            heading_path=metadata.get("heading_path", []),
            content=metadata.get("content", ""),
            source_path=Path(metadata["source_path"]),
        )

    @staticmethod
    def _matches_filters(chunk: DocChunk, filters: SearchFilters) -> bool:
        if filters.author and chunk.author != filters.author:
            return False
        if filters.contributor and chunk.contributor != filters.contributor:
            return False
        if filters.session_id and chunk.session_id != filters.session_id:
            return False
        if filters.doc_type and chunk.doc_type != filters.doc_type:
            return False
        if filters.tags and not all(tag in chunk.tags for tag in filters.tags):
            return False
        return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_sqlite_index.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents_dev/docs/indexer tests/docs/test_sqlite_index.py
git commit -m "feat(docs): add SQLite FTS5 keyword index backend

- IndexBackend ABC
- SQLiteFTS5Index with content indexing and metadata filtering
- baseline keyword search without external dependencies

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Hybrid Searcher

**Files:**
- Create: `agents_dev/docs/indexer/hybrid.py`
- Create: `tests/docs/test_hybrid_searcher.py`

**Interfaces:**
- Consumes: `IndexBackend`, `DocChunk`, `SearchFilters`, `SearchResult`
- Produces: `HybridSearcher` with `search(query: str, mode: str, filters: SearchFilters) -> SearchResult`

- [ ] **Step 1: Write failing hybrid searcher tests**

Create `tests/docs/test_hybrid_searcher.py`:

```python
"""Tests for HybridSearcher."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.indexer.hybrid import HybridSearcher
from agents_dev.docs.indexer.sqlite_idx import SQLiteFTS5Index
from agents_dev.docs.models import DocChunk, SearchFilters


@pytest.fixture
def hybrid(tmp_path):
    keyword = SQLiteFTS5Index(tmp_path / "kw.db")
    return HybridSearcher(keyword_backend=keyword)


def _chunk(doc_id: str, content: str) -> DocChunk:
    return DocChunk(
        chunk_id=f"{doc_id}_1",
        doc_id=doc_id,
        doc_title="Title",
        doc_type="how-to",
        author="alice",
        contributor=None,
        session_id="s1",
        tags=["api"],
        heading_path=["Title"],
        content=content,
        source_path=Path(f"{doc_id}.md"),
    )


def test_keyword_mode_delegates_to_backend(hybrid):
    hybrid.keyword_backend.index_chunks([_chunk("d1", "deploy production")])
    result = hybrid.search("deploy", mode="keyword", filters=SearchFilters())
    assert result.mode == "keyword"
    assert len(result.chunks) == 1
    assert result.total == 1


def test_hybrid_mode_falls_back_when_no_vector_backend(hybrid):
    hybrid.keyword_backend.index_chunks([_chunk("d1", "deploy production")])
    result = hybrid.search("deploy", mode="hybrid", filters=SearchFilters())
    assert result.mode == "hybrid"
    assert len(result.chunks) == 1


def test_invalid_mode_raises(hybrid):
    with pytest.raises(ValueError):
        hybrid.search("x", mode="invalid", filters=SearchFilters())
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/docs/test_hybrid_searcher.py -v
```

Expected: failures because module does not exist.

- [ ] **Step 3: Implement HybridSearcher**

Create `agents_dev/docs/indexer/hybrid.py`:

```python
"""Hybrid search dispatcher for DocHub."""

from __future__ import annotations

from typing import Dict, List, Optional

from agents_dev.docs.indexer.base import IndexBackend
from agents_dev.docs.models import DocChunk, SearchFilters, SearchResult

VALID_MODES = {"keyword", "semantic", "hybrid"}


class HybridSearcher:
    """Dispatches searches to keyword/vector backends and merges results."""

    def __init__(
        self,
        keyword_backend: IndexBackend,
        vector_backend: Optional[IndexBackend] = None,
        rrf_k: int = 60,
    ) -> None:
        self.keyword_backend = keyword_backend
        self.vector_backend = vector_backend
        self.rrf_k = rrf_k

    def search(
        self,
        query: str,
        mode: str,
        filters: SearchFilters,
    ) -> SearchResult:
        """Run a search across configured backends."""
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid search mode '{mode}'. Use one of {sorted(VALID_MODES)}")

        if mode == "semantic" and self.vector_backend is None:
            raise RuntimeError("Semantic search requires a vector backend")

        keyword_results: List[DocChunk] = []
        vector_results: List[DocChunk] = []

        if mode in {"keyword", "hybrid"}:
            keyword_results = self.keyword_backend.search(query, filters)

        if mode in {"semantic", "hybrid"} and self.vector_backend is not None:
            vector_results = self.vector_backend.search(query, filters)

        merged = self._rrf_merge(keyword_results, vector_results, filters.limit)
        return SearchResult(
            chunks=merged,
            total=len(merged),
            query=query,
            mode=mode,
        )

    def index_chunks(self, chunks: List[DocChunk]) -> None:
        """Index chunks in all available backends."""
        self.keyword_backend.index_chunks(chunks)
        if self.vector_backend is not None:
            self.vector_backend.index_chunks(chunks)

    def clear(self) -> None:
        """Clear all backends."""
        self.keyword_backend.clear()
        if self.vector_backend is not None:
            self.vector_backend.clear()

    def _rrf_merge(
        self,
        keyword_results: List[DocChunk],
        vector_results: List[DocChunk],
        limit: int,
    ) -> List[DocChunk]:
        """Merge keyword and vector results using Reciprocal Rank Fusion."""
        scores: Dict[str, float] = {}
        chunk_by_id: Dict[str, DocChunk] = {}

        for rank, chunk in enumerate(keyword_results):
            chunk_by_id[chunk.chunk_id] = chunk
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank + 1)

        for rank, chunk in enumerate(vector_results):
            chunk_by_id[chunk.chunk_id] = chunk
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank + 1)

        sorted_ids = sorted(scores, key=scores.get, reverse=True)[:limit]
        return [chunk_by_id[chunk_id] for chunk_id in sorted_ids]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_hybrid_searcher.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents_dev/docs/indexer/hybrid.py tests/docs/test_hybrid_searcher.py
git commit -m "feat(docs): add HybridSearcher

- dispatch keyword/semantic/hybrid search modes
- RRF merge of keyword and vector results
- graceful fallback when vector backend unavailable

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Dynamic Prompt Templates

**Files:**
- Create: `agents_dev/docs/prompts/__init__.py`
- Create: `agents_dev/docs/prompts/loader.py`
- Create: `agents_dev/docs/prompts/templates/search_context.j2`
- Create: `agents_dev/docs/prompts/templates/rag_answer.j2`
- Create: `tests/docs/test_prompt_renderer.py`

**Interfaces:**
- Produces: `PromptRenderer` with `render(template_name: str, **context) -> str`

- [ ] **Step 1: Write failing prompt renderer tests**

Create `tests/docs/test_prompt_renderer.py`:

```python
"""Tests for PromptRenderer."""

from pathlib import Path

from agents_dev.docs.models import DocChunk
from agents_dev.docs.prompts.loader import PromptRenderer


def test_render_search_context(tmp_path):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "search_context.j2").write_text(
        "Query: {{ query }}\n{% for c in chunks %}{{ c.content }}\n{% endfor %}"
    )
    renderer = PromptRenderer(templates_dir)
    chunk = DocChunk(
        chunk_id="c1",
        doc_id="d1",
        doc_title="Title",
        doc_type="how-to",
        author="alice",
        contributor=None,
        session_id=None,
        tags=[],
        heading_path=[],
        content="Run pytest.",
        source_path=Path("d1.md"),
    )
    text = renderer.render("search_context", query="how to deploy", chunks=[chunk])
    assert "how to deploy" in text
    assert "Run pytest." in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/docs/test_prompt_renderer.py -v
```

Expected: failure because module does not exist.

- [ ] **Step 3: Implement prompt renderer and templates**

Create `agents_dev/docs/prompts/__init__.py`:

```python
"""DocHub prompt templates."""

from __future__ import annotations
```

Create `agents_dev/docs/prompts/loader.py`:

```python
"""Jinja2-based prompt template renderer for DocHub."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptRenderer:
    """Load and render Jinja2 prompt templates."""

    def __init__(self, templates_path: Path) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @classmethod
    def default(cls) -> "PromptRenderer":
        """Return a renderer using built-in templates."""
        base = Path(__file__).parent / "templates"
        return cls(base)

    def render(self, template_name: str, **context: Any) -> str:
        """Render a named template with the given context."""
        template = self.env.get_template(f"{template_name}.j2")
        return template.render(**context)
```

Create `agents_dev/docs/prompts/templates/search_context.j2`:

```jinja2
{% if query %}用户问题：{{ query }}

{% endif %}以下是知识库中检索到的相关文档片段：
{% for chunk in chunks %}
---
[来源] {{ chunk.doc_title }}
[类型] {{ chunk.doc_type }}
{% if chunk.contributor %}[贡献者] {{ chunk.contributor }}{% else %}[作者] {{ chunk.author }}{% endif %}
{% if chunk.session_id %}[会话] {{ chunk.session_id }}{% endif %}
{% if chunk.heading_path %}[路径] {{ chunk.heading_path | join(' > ') }}{% endif %}
{{ chunk.content }}
{% endfor %}
```

Create `agents_dev/docs/prompts/templates/rag_answer.j2`:

```jinja2
你是团队知识库助手。请根据以下文档片段回答问题。

{% include 'search_context.j2' %}

请基于以上信息，用中文给出清晰、准确的回答。如果文档中没有相关信息，请明确说明。
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_prompt_renderer.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents_dev/docs/prompts tests/docs/test_prompt_renderer.py
git commit -m "feat(docs): add dynamic Jinja2 prompt templates

- PromptRenderer with filesystem loader
- default search_context.j2 and rag_answer.j2 templates
- templates include document metadata and contributor info

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: MCP Server and Tools

**Files:**
- Create: `agents_dev/docs/mcp/__init__.py`
- Create: `agents_dev/docs/mcp/tools.py`
- Create: `agents_dev/docs/mcp/server.py`
- Create: `tests/docs/test_mcp_tools.py`

**Interfaces:**
- Consumes: `DocumentStore`, `HybridSearcher`, `PromptRenderer`
- Produces: `DocHubTool` (ToolBase) exposing `function_definitions` and `run()`
- Produces: `DocHubMCPServer` (MCPServerBase)

- [ ] **Step 1: Write failing MCP tool tests**

Create `tests/docs/test_mcp_tools.py`:

```python
"""Tests for DocHub MCP tools."""

from datetime import datetime
from pathlib import Path

import pytest

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.server import DocHubMCPServer
from agents_dev.docs.mcp.tools import DocHubTool
from agents_dev.docs.models import MasterDocument


@pytest.fixture
def tool(tmp_path):
    config = DocHubConfig({"name": "test-kb"}, base_path=tmp_path)
    return DocHubTool(config)


def test_doc_create_and_read(tool, tmp_path):
    result = tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest.",
        "author": "alice",
        "doc_type": "how-to",
        "tags": ["api"],
    })
    assert result["doc_id"] == "api_deploy"

    read_result = tool.run("doc_read", {"doc_id": "api_deploy"})
    assert "Run pytest." in read_result["content"]


def test_doc_search(tool):
    tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest before deploy.",
        "author": "alice",
        "doc_type": "how-to",
    })
    result = tool.run("doc_search", {"query": "pytest", "mode": "keyword"})
    assert result["total"] >= 1


def test_doc_addendum(tool):
    tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest.",
        "author": "alice",
        "doc_type": "how-to",
    })
    tool.run("doc_add_addendum", {
        "parent_doc_id": "api_deploy",
        "contributor": "bob",
        "content": "Use Docker.",
        "summary": "Docker notes",
    })
    master = tool.run("doc_read", {"doc_id": "api_deploy"})
    assert "bob" in master["addendums"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/docs/test_mcp_tools.py -v
```

Expected: failures because modules do not exist.

- [ ] **Step 3: Implement MCP tools and server**

Create `agents_dev/docs/mcp/__init__.py`:

```python
"""DocHub MCP server and tools."""

from __future__ import annotations
```

Create `agents_dev/docs/mcp/tools.py`:

```python
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


def _to_doc_id(title: str) -> str:
    return "_".join(
        part.lower()
        for part in title.replace("-", " ").replace("_", " ").split()
        if part.isalnum() or part
    )


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
```

Create `agents_dev/docs/mcp/server.py`:

```python
"""DocHub MCP server implementation."""

from __future__ import annotations

from typing import Any, Dict

from core.mcp_base.server import MCPServerBase

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool


class DocHubMCPServer(MCPServerBase):
    """MCP server that exposes DocHub document management and search tools."""

    def __init__(self, config: DocHubConfig) -> None:
        super().__init__(name="dochub", version="1.0.0")
        self.config = config
        self.register_tool(DocHubTool(config))

    def get_server_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": "DocHub team knowledge-base server",
            "config_path": str(self.config.base_path / "dochub.yaml"),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_mcp_tools.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents_dev/docs/mcp tests/docs/test_mcp_tools.py
git commit -m "feat(docs): add DocHub MCP server and tools

- DocHubTool exposes search, query, read, create, update, addendum tools
- DocHubMCPServer registers DocHubTool
- auto-reindex on document mutations

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: CLI Commands

**Files:**
- Create: `cli/docs_cmd.py`
- Modify: `cli/main.py`
- Create: `tests/docs/test_cli.py`

**Interfaces:**
- Consumes: `DocHubConfig`, `DocHubTool`, `DocumentStore`
- Produces: Click command group `docs` registered on `agents-dev`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/docs/test_cli.py`:

```python
"""Tests for agents-dev docs CLI."""

from click.testing import CliRunner

from cli.main import main


def test_docs_init_creates_structure():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        result = runner.invoke(main, ["docs", "init", "--path", fs])
        assert result.exit_code == 0
        assert "Initialized" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/docs/test_cli.py -v
```

Expected: failure because `docs` command does not exist.

- [ ] **Step 3: Implement CLI commands**

Create `cli/docs_cmd.py`:

```python
"""agents-dev docs subcommand group for DocHub."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool

console = Console()


def _load_config(path: Path) -> DocHubConfig:
    yaml_path = Path(path) / "dochub.yaml"
    if not yaml_path.exists():
        raise click.ClickException(f"No dochub.yaml found at {yaml_path}")
    return DocHubConfig.from_yaml(yaml_path)


@click.group("docs")
def docs_cmd() -> None:
    """Manage the DocHub knowledge base."""


@docs_cmd.command("init")
@click.option("--path", "-p", default=".", help="Path to initialize the knowledge base")
def init_cmd(path: str) -> None:
    """Initialize a new DocHub knowledge base."""
    base = Path(path)
    base.mkdir(parents=True, exist_ok=True)
    (base / "docs" / "master").mkdir(parents=True, exist_ok=True)
    (base / "docs" / "addendums").mkdir(parents=True, exist_ok=True)
    (base / "index").mkdir(parents=True, exist_ok=True)
    (base / "sessions").mkdir(parents=True, exist_ok=True)

    config_path = base / "dochub.yaml"
    if not config_path.exists():
        config_path.write_text(
            "name: dochub\nversion: \"1.0.0\"\n"
            "index:\n  keyword:\n    backend: sqlite\n"
            "chunking:\n  size: 512\n  overlap: 100\n"
            "search:\n  default_mode: keyword\n  top_k: 10\n",
            encoding="utf-8",
        )

    console.print(f"[green]Initialized DocHub at[/green] {base.absolute()}")


@docs_cmd.command("add")
@click.argument("kind", type=click.Choice(["master"]))
@click.option("--title", required=True, help="Document title")
@click.option("--author", required=True, help="Document author")
@click.option("--type", "doc_type", required=True, type=click.Choice(["tutorial", "how-to", "reference", "explanation"]))
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--session-id", default=None, help="Session ID")
@click.option("--summary", default=None, help="Document summary")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="Markdown file to ingest")
@click.option("--config", "-c", default=".", help="Path to DocHub base directory")
def add_cmd(
    kind: str,
    title: str,
    author: str,
    doc_type: str,
    tags: str,
    session_id: Optional[str],
    summary: Optional[str],
    file_path: str,
    config: str,
) -> None:
    """Add a master document to the knowledge base."""
    cfg = _load_config(config)
    tool = DocHubTool(cfg)
    content = Path(file_path).read_text(encoding="utf-8")
    result = tool.run("doc_create", {
        "title": title,
        "content": content,
        "author": author,
        "doc_type": doc_type,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "session_id": session_id,
        "summary": summary,
    })
    console.print(f"[green]Created {kind} document[/green] {result['doc_id']}")


@docs_cmd.command("search")
@click.argument("query")
@click.option("--mode", default="keyword", type=click.Choice(["keyword", "semantic", "hybrid"]))
@click.option("--author", default=None)
@click.option("--contributor", default=None)
@click.option("--session-id", default=None)
@click.option("--doc-type", default=None)
@click.option("--limit", default=10, type=int)
@click.option("--config", "-c", default=".")
def search_cmd(
    query: str,
    mode: str,
    author: Optional[str],
    contributor: Optional[str],
    session_id: Optional[str],
    doc_type: Optional[str],
    limit: int,
    config: str,
) -> None:
    """Search the DocHub knowledge base."""
    cfg = _load_config(config)
    tool = DocHubTool(cfg)
    filters = {
        "author": author,
        "contributor": contributor,
        "session_id": session_id,
        "doc_type": doc_type,
        "limit": limit,
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    result = tool.run("doc_search", {"query": query, "mode": mode, "filters": filters, "limit": limit})
    console.print(f"Found {result['total']} results for '{result['query']}'")
    for chunk in result["chunks"]:
        console.print(f"- [bold]{chunk['doc_title']}[/bold] ({chunk['doc_type']})")
        console.print(f"  {chunk['content'][:200]}...")


@docs_cmd.command("ask")
@click.argument("question")
@click.option("--session-id", default=None)
@click.option("--config", "-c", default=".")
def ask_cmd(question: str, session_id: Optional[str], config: str) -> None:
    """Ask a question using RAG over the knowledge base."""
    cfg = _load_config(config)
    tool = DocHubTool(cfg)
    filters = {"session_id": session_id} if session_id else {}
    result = tool.run("doc_query", {"question": question, "filters": filters})
    console.print("[bold]Generated prompt for LLM:[/bold]")
    console.print(result["prompt"])


@docs_cmd.command("serve")
@click.option("--config", "-c", default=".", help="Path to DocHub base directory")
@click.option("--transport", default="stdio", type=click.Choice(["stdio"]))
def serve_cmd(config: str, transport: str) -> None:
    """Start the DocHub MCP server."""
    cfg = _load_config(config)
    if transport != "stdio":
        raise click.ClickException("Only stdio transport is supported")
    console.print(f"[green]Starting DocHub MCP server[/green] ({cfg.base_path})")
    from agents_dev.docs.mcp.server import DocHubMCPServer
    server = DocHubMCPServer(cfg)
    console.print(f"Server info: {server.get_server_info()}")
```

Modify `cli/main.py` to register `docs_cmd`:

```python
"""CLI main entry point for agents-dev.

Provides the top-level Click group and registers all subcommands.
"""

from __future__ import annotations

import click

from cli.create_cmd import create_cmd
from cli.docs_cmd import docs_cmd
from cli.export_cmd import export_cmd
from cli.generate_cmd import generate_cmd
from cli.list_cmd import list_cmd
from cli.validate_cmd import validate_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="agents-dev")
def main() -> None:
    """agents-dev -- Multi-tool agent/skill development environment."""


# Register all subcommands
main.add_command(create_cmd)
main.add_command(generate_cmd)
main.add_command(export_cmd)
main.add_command(validate_cmd)
main.add_command(list_cmd)
main.add_command(docs_cmd)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_cli.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add cli/docs_cmd.py cli/main.py tests/docs/test_cli.py
git commit -m "feat(docs): add agents-dev docs CLI commands

- init, add, search, ask, serve subcommands
- load DocHubConfig from dochub.yaml
- register docs command group on main CLI

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Integration Tests and Final Verification

**Files:**
- Create: `tests/docs/test_integration.py`
- Modify: `pyproject.toml` package discovery if needed

**Interfaces:**
- Verifies: CLI + Store + Chunker + Index + MCP tools work end-to-end

- [ ] **Step 1: Write integration tests**

Create `tests/docs/test_integration.py`:

```python
"""Integration tests for DocHub end-to-end workflows."""

from pathlib import Path

from click.testing import CliRunner

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool
from cli.main import main


def test_full_cli_workflow():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        init_result = runner.invoke(main, ["docs", "init", "--path", fs])
        assert init_result.exit_code == 0

        doc_file = Path(fs) / "deploy.md"
        doc_file.write_text("Run pytest before deploying.", encoding="utf-8")

        add_result = runner.invoke(main, [
            "docs", "add", "master",
            "--title", "API Deploy",
            "--author", "alice",
            "--type", "how-to",
            "--tags", "api,deploy",
            "--file", str(doc_file),
            "--config", fs,
        ])
        assert add_result.exit_code == 0

        search_result = runner.invoke(main, [
            "docs", "search", "pytest",
            "--mode", "keyword",
            "--config", fs,
        ])
        assert search_result.exit_code == 0
        assert "Found" in search_result.output


def test_mcp_tool_full_workflow(tmp_path):
    config = DocHubConfig({"name": "test-kb"}, base_path=tmp_path)
    tool = DocHubTool(config)

    tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest before deploy.",
        "author": "alice",
        "doc_type": "how-to",
        "tags": ["api"],
    })
    tool.run("doc_add_addendum", {
        "parent_doc_id": "api_deploy",
        "contributor": "bob",
        "content": "Use docker compose up.",
        "summary": "Docker deploy",
    })

    result = tool.run("doc_search", {"query": "docker", "mode": "keyword"})
    assert result["total"] >= 1

    read = tool.run("doc_read", {"doc_id": "api_deploy"})
    assert "bob" in read["addendums"]
```

- [ ] **Step 2: Run tests to verify they pass**

Run:

```bash
pytest tests/docs/test_integration.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Update pyproject.toml package discovery**

Ensure `pyproject.toml` includes `agents_dev*`:

```toml
[tool.setuptools.packages.find]
include = ["core*", "cli*", "migration*", "formats*", "agents_dev*"]
```

- [ ] **Step 4: Run full test suite**

Run:

```bash
pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/docs/test_integration.py pyproject.toml
git commit -m "test(docs): add DocHub integration tests

- CLI end-to-end workflow test
- MCP tool search + addendum integration test
- update package discovery for agents_dev

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

### Spec Coverage

| Spec Section | Implementing Task |
|---|---|
| Errors (§12) | Task 1 |
| Models (§2) | Task 1 |
| Config (§13) | Task 1 |
| Store / directory structure (§3) | Task 2 |
| Markdown parsing (§8.1) | Task 2 |
| Chunker (§5.3, §8.1) | Task 3 |
| SQLite FTS5 baseline (§5.1, §11.3) | Task 4 |
| Hybrid search / RRF (§5.4) | Task 5 |
| Prompt templates (§7) | Task 6 |
| MCP tools / server (§6) | Task 7 |
| CLI (§9) | Task 8 |
| Integration tests (§15) | Task 9 |

### Placeholder Scan

No TBD, TODO, "implement later", or "appropriate error handling" placeholders found.

### Type Consistency

- `MasterDocument`, `Addendum`, `DocChunk`, `SearchFilters`, `SearchResult` used consistently.
- `DocHubConfig.templates_path` returns `Path`.
- `DocumentStore` accepts and returns model instances.
- `HybridSearcher` accepts `IndexBackend` ABC instances.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-26-dochub-implementation-plan.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using `executing-plans`, batch execution with checkpoints.

Which approach would you like to use?
