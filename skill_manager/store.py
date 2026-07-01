from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import shutil

from skill_manager.errors import StorageError
from skill_manager.models import ProjectOverride, PromptFragment, Skill, TriggerRule


class SkillStore(ABC):
    @abstractmethod
    def list_skills(self, filters: dict | None = None) -> list[Skill]: ...

    @abstractmethod
    def get_skill(self, name: str) -> Skill | None: ...

    @abstractmethod
    def save_skill(self, skill: Skill) -> None: ...

    @abstractmethod
    def delete_skill(self, name: str) -> None: ...

    @abstractmethod
    def list_fragments(self, skill_name: str, filters: dict | None = None) -> list[PromptFragment]: ...

    @abstractmethod
    def save_fragment(self, fragment: PromptFragment) -> None: ...

    @abstractmethod
    def delete_fragment(self, fragment_id: str) -> None: ...

    @abstractmethod
    def list_project_overrides(self, project_path: str) -> list[ProjectOverride]: ...

    @abstractmethod
    def save_project_override(self, override: ProjectOverride) -> None: ...


class FileSystemStore(SkillStore):
    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.skills_dir = self.root / "skills"
        self.overrides_dir = self.root / "overrides"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.overrides_dir.mkdir(parents=True, exist_ok=True)

    def _skill_dir(self, name: str) -> Path:
        return self.skills_dir / name

    def _skill_path(self, name: str) -> Path:
        return self._skill_dir(name) / "skill.json"

    def _base_prompt_path(self, name: str) -> Path:
        return self._skill_dir(name) / "base_prompt.md"

    def _fragments_dir(self, name: str) -> Path:
        return self._skill_dir(name) / "fragments"

    def _override_dir(self, project_path: str) -> Path:
        key = self._project_key(project_path)
        return self.overrides_dir / key

    @staticmethod
    def _project_key(project_path: str) -> str:
        return str(hash(os.path.normpath(project_path)))

    def list_skills(self, filters: dict | None = None) -> list[Skill]:
        filters = filters or {}
        skills: list[Skill] = []
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill = self._load_skill_from_dir(skill_dir)
            if skill is None:
                continue
            if filters.get("language") and filters["language"] not in skill.supported_languages and "*" not in skill.supported_languages:
                continue
            if filters.get("action") and skill.default_action != filters["action"]:
                continue
            if filters.get("tag") and filters["tag"] not in skill.tags:
                continue
            skills.append(skill)
        return skills

    def get_skill(self, name: str) -> Skill | None:
        skill_dir = self._skill_dir(name)
        if not skill_dir.exists():
            return None
        return self._load_skill_from_dir(skill_dir)

    def _load_skill_from_dir(self, skill_dir: Path) -> Skill | None:
        skill_path = skill_dir / "skill.json"
        if not skill_path.exists():
            return None
        try:
            data = json.loads(skill_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise StorageError(f"Failed to read skill from {skill_path}: {exc}") from exc

        base_prompt_path = skill_dir / "base_prompt.md"
        base_prompt = base_prompt_path.read_text(encoding="utf-8") if base_prompt_path.exists() else ""

        triggers = [TriggerRule(**t) for t in data.get("triggers", [])]

        return Skill(
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

    def save_skill(self, skill: Skill) -> None:
        skill_dir = self._skill_dir(skill.name)
        skill_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "name": skill.name,
            "description": skill.description,
            "version": skill.version,
            "default_action": skill.default_action,
            "supported_languages": skill.supported_languages,
            "tags": skill.tags,
            "triggers": [{"type": t.type, "value": t.value, "action": t.action, "language_hint": t.language_hint} for t in skill.triggers],
            "created_at": skill.created_at,
            "updated_at": skill.updated_at,
        }
        try:
            (skill_dir / "skill.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            (skill_dir / "base_prompt.md").write_text(skill.base_prompt, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write skill {skill.name}: {exc}") from exc

    def delete_skill(self, name: str) -> None:
        skill_dir = self._skill_dir(name)
        if skill_dir.exists():
            try:
                shutil.rmtree(skill_dir)
            except OSError as exc:
                raise StorageError(f"Failed to delete skill {name}: {exc}") from exc

    def list_fragments(self, skill_name: str, filters: dict | None = None) -> list[PromptFragment]:
        filters = filters or {}
        fragments_dir = self._fragments_dir(skill_name)
        if not fragments_dir.exists():
            return []

        fragments: list[PromptFragment] = []
        for fragment_file in sorted(fragments_dir.glob("*.md")):
            fragment = self._load_fragment(fragment_file, skill_name)
            if fragment is None:
                continue
            if filters.get("language") and fragment.language != filters["language"]:
                continue
            if filters.get("action") and fragment.action != filters["action"]:
                continue
            if filters.get("trigger") and fragment.trigger != filters["trigger"]:
                continue
            fragments.append(fragment)
        return fragments

    def _load_fragment(self, path: Path, skill_name: str) -> PromptFragment | None:
        meta_path = path.with_suffix(".json")
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to read fragment content from {path}: {exc}") from exc
        meta: dict[str, Any] = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise StorageError(f"Failed to read fragment metadata from {meta_path}: {exc}") from exc

        return PromptFragment(
            id=meta.get("id", path.stem),
            skill_name=skill_name,
            language=meta.get("language"),
            action=meta.get("action"),
            trigger=meta.get("trigger"),
            priority=meta.get("priority", 0),
            content=content,
            is_required=meta.get("is_required", False),
        )

    def save_fragment(self, fragment: PromptFragment) -> None:
        fragments_dir = self._fragments_dir(fragment.skill_name)
        fragments_dir.mkdir(parents=True, exist_ok=True)

        base_name = fragment.id or "fragment"
        content_path = fragments_dir / f"{base_name}.md"
        meta_path = fragments_dir / f"{base_name}.json"

        meta = {
            "id": fragment.id,
            "language": fragment.language,
            "action": fragment.action,
            "trigger": fragment.trigger,
            "priority": fragment.priority,
            "is_required": fragment.is_required,
        }
        try:
            content_path.write_text(fragment.content, encoding="utf-8")
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write fragment {fragment.id}: {exc}") from exc

    def delete_fragment(self, fragment_id: str) -> None:
        # Fragment deletion requires skill_name context; this base method is intentionally broad.
        for skill_dir in self.skills_dir.iterdir():
            fragments_dir = skill_dir / "fragments"
            for ext in (".md", ".json"):
                candidate = fragments_dir / f"{fragment_id}{ext}"
                if candidate.exists():
                    try:
                        candidate.unlink()
                    except OSError as exc:
                        raise StorageError(f"Failed to delete fragment {fragment_id}: {exc}") from exc

    def list_project_overrides(self, project_path: str) -> list[ProjectOverride]:
        override_dir = self._override_dir(project_path)
        if not override_dir.exists():
            return []

        overrides: list[ProjectOverride] = []
        for skill_dir in override_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_name = skill_dir.name
            for fragment_file in sorted(skill_dir.glob("*.md")):
                fragment = self._load_fragment(fragment_file, skill_name)
                if fragment is None:
                    continue
                overrides.append(ProjectOverride(skill_name=skill_name, project_path=project_path, fragment=fragment))
        return overrides

    def save_project_override(self, override: ProjectOverride) -> None:
        override_dir = self._override_dir(override.project_path) / override.skill_name
        override_dir.mkdir(parents=True, exist_ok=True)

        fragment = override.fragment
        base_name = fragment.id or "override"
        content_path = override_dir / f"{base_name}.md"
        meta_path = override_dir / f"{base_name}.json"

        meta = {
            "id": fragment.id,
            "language": fragment.language,
            "action": fragment.action,
            "trigger": fragment.trigger,
            "priority": fragment.priority,
            "is_required": fragment.is_required,
        }
        try:
            content_path.write_text(fragment.content, encoding="utf-8")
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write project override: {exc}") from exc
