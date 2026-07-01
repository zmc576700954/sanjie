from skill_manager.models import Skill, PromptFragment, TriggerRule, ResolveResult


def test_skill_creation():
    skill = Skill(
        name="code_review",
        description="Review code",
        version="1.0.0",
        base_prompt="Review this code.",
        default_action="self_review",
        supported_languages=["python", "*"],
        tags=["review"],
        triggers=[TriggerRule(type="slash", value="/review", action="self_review")],
    )
    assert skill.name == "code_review"
    assert skill.default_action == "self_review"


def test_fragment_match_score():
    f = PromptFragment(
        id="f1",
        skill_name="code_review",
        language="python",
        action="self_review",
        trigger="/review",
        priority=10,
        content="Use type hints.",
        is_required=False,
    )
    assert f.match_score(language="python", action="self_review", trigger="/review") == 3
    assert f.match_score(language="python") == 1
    assert f.match_score() == 0


def test_resolve_result_serialization():
    result = ResolveResult(
        skill="code_review",
        resolved_for={"language": "python", "action": "self_review", "trigger": "/review"},
        prompt="Final prompt",
        fragments_applied=["f1"],
        fallback_used=False,
        warnings=[],
    )
    assert result.to_dict()["fallback_used"] is False
