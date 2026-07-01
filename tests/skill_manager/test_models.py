# tests/skill_manager/test_models.py
from skill_manager.errors import SkillManagerError, SkillNotFoundError


def test_skill_not_found_is_skill_manager_error():
    err = SkillNotFoundError("foo")
    assert isinstance(err, SkillManagerError)
    assert str(err) == "foo"
