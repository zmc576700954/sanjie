from pathlib import Path

from skill_manager.models import PromptFragment, ProjectOverride, Skill, TriggerRule
from skill_manager.resolver import PriorityResolver
from skill_manager.store import FileSystemStore


def test_falls_back_to_base_prompt(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    store.save_skill(Skill(name="code_review", description="Review", version="1.0.0", base_prompt="Base prompt."))

    resolver = PriorityResolver(store)
    result = resolver.resolve("code_review")

    assert result.prompt == "Base prompt."
    assert result.fallback_used is True


def test_assembles_matching_fragments(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    store.save_skill(Skill(
        name="code_review",
        description="Review",
        version="1.0.0",
        base_prompt="Base prompt.",
        default_action="self_review",
        triggers=[TriggerRule(type="slash", value="/review", action="self_review")],
    ))
    store.save_fragment(PromptFragment(
        id="py",
        skill_name="code_review",
        language="python",
        content="Python specific.",
    ))
    store.save_fragment(PromptFragment(
        id="self",
        skill_name="code_review",
        action="self_review",
        content="Self review specific.",
        priority=5,
    ))

    resolver = PriorityResolver(store)
    result = resolver.resolve("code_review", language="python", action="self_review", trigger="/review")

    assert "Base prompt." in result.prompt
    assert "Python specific." in result.prompt
    assert "Self review specific." in result.prompt
    assert result.fallback_used is False


def test_project_override_wins(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    store.save_skill(Skill(name="code_review", description="Review", version="1.0.0", base_prompt="Base prompt."))
    store.save_project_override(ProjectOverride(
        skill_name="code_review",
        project_path=str(tmp_path),
        fragment=PromptFragment(
            id="override",
            skill_name="code_review",
            content="Project override.",
            is_required=True,
        ),
    ))

    resolver = PriorityResolver(store)
    result = resolver.resolve("code_review", project_path=str(tmp_path))

    assert "Project override." in result.prompt


def test_is_required_always_included(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    store.save_skill(Skill(name="code_review", description="Review", version="1.0.0", base_prompt="Base prompt."))
    store.save_fragment(PromptFragment(
        id="required_frag",
        skill_name="code_review",
        language="java",  # different from query context
        content="Always include this.",
        is_required=True,
    ))

    resolver = PriorityResolver(store)
    # Pass language=python, but fragment is for java — without is_required it would be filtered out
    result = resolver.resolve("code_review", language="python")

    assert "Always include this." in result.prompt
    assert "required_frag" in result.fragments_applied


def test_fallback_used_when_no_fragments_match_with_all_context(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    store.save_skill(Skill(
        name="code_review",
        description="Review",
        version="1.0.0",
        base_prompt="Base prompt.",
        default_action="self_review",
        triggers=[TriggerRule(type="slash", value="/review", action="self_review")],
    ))
    store.save_fragment(PromptFragment(
        id="py",
        skill_name="code_review",
        language="python",
        content="Python specific.",
    ))

    resolver = PriorityResolver(store)
    # Provide all context but nothing matches (language=java, action=other, trigger=/other)
    result = resolver.resolve("code_review", language="java", action="other", trigger="/other")

    assert result.prompt == "Base prompt."
    assert result.fallback_used is True
