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
