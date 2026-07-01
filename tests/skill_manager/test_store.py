from pathlib import Path

from skill_manager.builtin_skills import load_builtin_skills
from skill_manager.store import FileSystemStore


def test_load_builtin_skills(tmp_path: Path):
    source_root = Path(__file__).parent.parent.parent / "skill_manager" / "builtin_skills"
    store = FileSystemStore(str(tmp_path))
    load_builtin_skills(store, str(source_root))

    skill = store.get_skill("code_review")
    assert skill is not None
    assert "python" in skill.supported_languages

    fragments = store.list_fragments("code_review")
    languages = {f.language for f in fragments}
    assert "python" in languages
