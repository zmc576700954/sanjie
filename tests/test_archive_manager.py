from skills.tool_taibai.scripts.archive_manager import archive_file


class TestArchiveManager:
    def test_archive_success(self, tmp_path):
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        index_file = docs_root / "MEMORY_INDEX.md"
        index_file.write_text("# Index\n", encoding="utf-8")

        source = tmp_path / "source.md"
        source.write_text("content", encoding="utf-8")

        result = archive_file(str(source), "topic", "summary", docs_root=str(docs_root))
        assert result is True
        assert not source.exists()
        assert (docs_root / "archive" / "source.md").exists()

        index_content = index_file.read_text(encoding="utf-8")
        assert "topic" in index_content
        assert "summary" in index_content

    def test_archive_file_not_found(self, tmp_path):
        result = archive_file(str(tmp_path / "nonexistent.md"), "topic", "summary")
        assert result is False

    def test_archive_relative_path_dynamic(self, tmp_path):
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        index_file = docs_root / "MEMORY_INDEX.md"
        index_file.write_text("", encoding="utf-8")

        source = tmp_path / "source.md"
        source.write_text("content", encoding="utf-8")

        archive_file(str(source), "topic", "summary", docs_root=str(docs_root))
        index_content = index_file.read_text(encoding="utf-8")
        assert "docs/archive/source.md" in index_content
