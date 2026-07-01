from __future__ import annotations

from skill_manager.errors import SkillNotFoundError
from skill_manager.models import PromptFragment, ResolveResult, Skill
from skill_manager.store import SkillStore


class PriorityResolver:
    def __init__(self, store: SkillStore) -> None:
        self.store = store

    def resolve(
        self,
        name: str,
        language: str | None = None,
        action: str | None = None,
        trigger: str | None = None,
        project_path: str | None = None,
    ) -> ResolveResult:
        skill = self.store.get_skill(name)
        if skill is None:
            available = [s.name for s in self.store.list_skills()]
            raise SkillNotFoundError(f"Skill '{name}' not found. Available: {available}")

        resolved_language = language
        resolved_action = action
        resolved_trigger = trigger
        warnings: list[str] = []

        fragments: list[PromptFragment] = []

        if project_path:
            overrides = self.store.list_project_overrides(project_path)
            for override in overrides:
                if override.skill_name == name:
                    fragments.append(override.fragment)

        skill_fragments = self.store.list_fragments(name)

        # Group by match score and collect in priority order
        score_buckets: dict[int, list[PromptFragment]] = {}
        required_fragments: list[PromptFragment] = []
        for fragment in skill_fragments:
            if fragment.is_required:
                required_fragments.append(fragment)
                continue
            score = fragment.match_score(language=language, action=action, trigger=trigger)
            if score == 0:
                continue
            score_buckets.setdefault(score, []).append(fragment)

        for score in sorted(score_buckets.keys(), reverse=True):
            bucket = sorted(score_buckets[score], key=lambda f: f.priority, reverse=True)
            fragments.extend(bucket)

        # Append required fragments after scored ones
        fragments.extend(required_fragments)

        # Deduplicate by id while preserving order
        seen: set[str] = set()
        unique_fragments: list[PromptFragment] = []
        for fragment in fragments:
            if fragment.id in seen:
                continue
            seen.add(fragment.id)
            unique_fragments.append(fragment)

        fallback_used = not unique_fragments

        parts = [skill.base_prompt.strip()]
        for fragment in unique_fragments:
            parts.append(fragment.content.strip())

        prompt = "\n\n".join(parts)

        return ResolveResult(
            skill=name,
            resolved_for={
                "language": resolved_language,
                "action": resolved_action,
                "trigger": resolved_trigger,
            },
            prompt=prompt,
            fragments_applied=[f.id for f in unique_fragments],
            fallback_used=fallback_used,
            warnings=warnings,
        )
