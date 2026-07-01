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
            old_snapshot = self.addendum_dir / f"{addendum_id}.v{len(master.addendums.get(contributor, Addendum(
                addendum_id=addendum_id,
                parent_doc_id=doc_id,
                contributor=contributor,
                summary="",
                created_at=now,
                updated_at=now,
                content_path=content_path,
            ).versions or [])) + 1}.md"
            shutil.copy2(content_path, old_snapshot)
            existing_versions = master.addendums.get(contributor, Addendum(
                addendum_id=addendum_id,
                parent_doc_id=doc_id,
                contributor=contributor,
                summary="",
                created_at=now,
                updated_at=now,
                content_path=content_path,
            )).versions or []
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
