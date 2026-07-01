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
