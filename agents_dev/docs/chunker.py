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
            section_chunks = self._split_into_size_chunks(section_text)
            for chunk_text in section_chunks:
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
                        content=chunk_text.strip(),
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
        """Split Markdown into (heading_path, section_text) pairs.

        Skips heading detection inside fenced code blocks.
        """
        lines = content.splitlines()
        sections: List[tuple[List[str], str]] = []
        current_path: List[str] = []
        current_lines: List[str] = []
        in_code_block = False

        def flush() -> None:
            if current_lines:
                sections.append((list(current_path), "\n".join(current_lines)))
                current_lines.clear()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                current_lines.append(line)
                continue
            if not in_code_block:
                match = re.match(r"^(#{1,6})\s+(.+)$", line)
                if match:
                    flush()
                    level = len(match.group(1))
                    title = match.group(2).strip()
                    current_path = current_path[: level - 1]
                    current_path.append(title)
                    continue
            current_lines.append(line)
        flush()

        if not sections:
            sections.append(([], content))

        return sections

    def _split_into_size_chunks(self, text: str) -> List[str]:
        """Split text into chunks of at most size characters with overlap."""
        if not text:
            return []
        if len(text) <= self.size:
            return [text]

        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.size, len(text))
            if end < len(text):
                # Try to break at a newline or space for cleaner splits
                nl_pos = text.rfind("\n", start, end)
                if nl_pos > start:
                    end = nl_pos + 1
                else:
                    space_pos = text.rfind(" ", start, end)
                    if space_pos > start:
                        end = space_pos + 1
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - self.overlap
            if start < 0:
                start = 0
            if start >= len(text):
                break
        return chunks
