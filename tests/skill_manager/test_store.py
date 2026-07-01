from pathlib import Path

import pytest

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
