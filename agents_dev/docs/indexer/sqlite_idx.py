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
