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
