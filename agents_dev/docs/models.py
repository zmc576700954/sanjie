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
