from __future__ import annotations

import json
from pathlib import Path

from skill_manager.models import PromptFragment, Skill, TriggerRule
from skill_manager.store import SkillStore


def load_builtin_skills(store: SkillStore, source_root: str | None = None) -> None:
    if source_root is None:
        source_root = str(Path(__file__).parent)

    root = Path(source_root)
    for skill_dir in root.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_path = skill_dir / "skill.json"
        if not skill_path.exists():
            continue

        data = json.loads(skill_path.read_text(encoding="utf-8"))
        base_prompt_path = skill_dir / "base_prompt.md"
        base_prompt = base_prompt_path.read_text(encoding="utf-8") if base_prompt_path.exists() else ""

        triggers = [TriggerRule(**t) for t in data.get("triggers", [])]

        skill = Skill(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            base_prompt=base_prompt,
            default_action=data.get("default_action"),
            supported_languages=data.get("supported_languages", ["*"]),
            tags=data.get("tags", []),
            triggers=triggers,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
        store.save_skill(skill)

        fragments_dir = skill_dir / "fragments"
        if fragments_dir.exists():
            for fragment_file in sorted(fragments_dir.glob("*.md")):
                meta_path = fragment_file.with_suffix(".json")
                meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
                content = fragment_file.read_text(encoding="utf-8")
                fragment = PromptFragment(
                    id=meta.get("id", fragment_file.stem),
                    skill_name=skill.name,
                    language=meta.get("language"),
                    action=meta.get("action"),
                    trigger=meta.get("trigger"),
                    priority=meta.get("priority", 0),
                    content=content,
                    is_required=meta.get("is_required", False),
                )
                store.save_fragment(fragment)
