from skill_manager.models import Skill, TriggerRule
from skill_manager.trigger import MultiStrategyTriggerResolver


def test_slash_trigger_match():
    skill = Skill(
        name="code_review",
        description="Review code",
        version="1.0.0",
        base_prompt="Base",
        triggers=[TriggerRule(type="slash", value="/review", action="self_review")],
    )
    resolver = MultiStrategyTriggerResolver()
    result = resolver.resolve("/review", None, skill)
    assert result.matched is True
    assert result.action == "self_review"


def test_keyword_trigger_match():
    skill = Skill(
        name="code_review",
        description="Review code",
        version="1.0.0",
        base_prompt="Base",
        triggers=[TriggerRule(type="keyword", value="review this code", action="peer_review")],
    )
    resolver = MultiStrategyTriggerResolver()
    result = resolver.resolve("can you review this code please?", None, skill)
    assert result.matched is True
    assert result.action == "peer_review"


def test_event_trigger_match():
    skill = Skill(
        name="code_review",
        description="Review code",
        version="1.0.0",
        base_prompt="Base",
        triggers=[TriggerRule(type="event", value="on_save", action="quick_review")],
    )
    resolver = MultiStrategyTriggerResolver()
    result = resolver.resolve(None, "on_save", skill)
    assert result.matched is True
    assert result.action == "quick_review"


def test_no_match_uses_default_action():
    skill = Skill(
        name="code_review",
        description="Review code",
        version="1.0.0",
        base_prompt="Base",
        default_action="self_review",
        triggers=[TriggerRule(type="slash", value="/review", action="self_review")],
    )
    resolver = MultiStrategyTriggerResolver()
    result = resolver.resolve("hello", None, skill)
    assert result.matched is False
    assert result.action == "self_review"
