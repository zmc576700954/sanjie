from pathlib import Path

import pytest

from skill_manager.errors import StorageError
from skill_manager.models import Skill, PromptFragment
from skill_manager.store import FileSystemStore


def test_file_system_store_round_trip(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    skill = Skill(name="code_review", description="Review code", version="1.0.0", base_prompt="Base")
    store.save_skill(skill)

    loaded = store.get_skill("code_review")
    assert loaded is not None
    assert loaded.name == "code_review"

    fragment = PromptFragment(
        id="f1",
        skill_name="code_review",
        language="python",
        content="Use type hints.",
    )
    store.save_fragment(fragment)

    fragments = store.list_fragments("code_review")
    assert len(fragments) == 1
    assert fragments[0].language == "python"


def test_load_fragment_raises_storage_error_on_missing_content(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    skill = Skill(name="test_skill", description="Test", version="1.0.0", base_prompt="Base")
    store.save_skill(skill)

    fragments_dir = tmp_path / "skills" / "test_skill" / "fragments"
    fragments_dir.mkdir(parents=True, exist_ok=True)
    content_path = fragments_dir / "frag.md"
    content_path.write_text("content", encoding="utf-8")

    # Remove the content file after listing has found it, but before _load_fragment reads it
    content_path.unlink()

    with pytest.raises(StorageError, match="Failed to read fragment content"):
        store._load_fragment(content_path, "test_skill")


def test_load_fragment_raises_storage_error_on_bad_metadata(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    skill = Skill(name="test_skill", description="Test", version="1.0.0", base_prompt="Base")
    store.save_skill(skill)

    fragments_dir = tmp_path / "skills" / "test_skill" / "fragments"
    fragments_dir.mkdir(parents=True, exist_ok=True)
    content_path = fragments_dir / "frag.md"
    content_path.write_text("content", encoding="utf-8")
    meta_path = fragments_dir / "frag.json"
    meta_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(StorageError, match="Failed to read fragment metadata"):
        store._load_fragment(content_path, "test_skill")


def test_delete_fragment_raises_storage_error_on_permission_denied(tmp_path: Path, monkeypatch):
    store = FileSystemStore(str(tmp_path))
    skill = Skill(name="test_skill", description="Test", version="1.0.0", base_prompt="Base")
    store.save_skill(skill)

    fragment = PromptFragment(
        id="frag1",
        skill_name="test_skill",
        language="python",
        content="content",
    )
    store.save_fragment(fragment)

    def mock_unlink(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "unlink", mock_unlink)

    with pytest.raises(StorageError, match="Failed to delete fragment"):
        store.delete_fragment("frag1")


def test_delete_skill_raises_storage_error_on_permission_denied(tmp_path: Path, monkeypatch):
    store = FileSystemStore(str(tmp_path))
    skill = Skill(name="test_skill", description="Test", version="1.0.0", base_prompt="Base")
    store.save_skill(skill)

    import shutil

    def mock_rmtree(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(shutil, "rmtree", mock_rmtree)

    with pytest.raises(StorageError, match="Failed to delete skill"):
        store.delete_skill("test_skill")
