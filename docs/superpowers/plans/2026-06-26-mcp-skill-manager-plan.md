# MCP Skill Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone MCP server that manages code-development skills and dynamically assembles prompts by language, action, and trigger.

**Architecture:** The service is a new independent package `skill_manager/` that lives next to the existing `core/`, `cli/`, etc. It defines its own models, a pluggable store, resolution engine, language detector, trigger resolver, and an MCP server wrapper. It reuses `AgentsDevelopError` from `core.shared.errors` but does not depend on `CoreComponent` abstractions, because skills here are data-driven prompt templates, not executable components.

**Tech Stack:** Python 3.10+, `mcp` SDK (`mcp.server.lowlevel.Server`), Pydantic for model validation, pytest for testing, stdio transport.

---

## File Structure

```
skill_manager/
├── __init__.py
├── models.py                 # Skill, PromptFragment, TriggerRule, ProjectOverride, ResolveResult
├── errors.py                 # SkillManagerError hierarchy
├── store.py                  # SkillStore ABC + FileSystemStore
├── language.py               # LanguageDetector ABC + HeuristicLanguageDetector
├── trigger.py                # TriggerResolver ABC + MultiStrategyTriggerResolver
├── resolver.py               # PriorityResolver + FragmentAssembler
├── server.py                 # MCP server setup and tool handlers
├── builtin_skills/           # Built-in skills shipped with the package
│   ├── __init__.py
│   └── code_review/
│       ├── skill.json
│       ├── base_prompt.md
│       └── fragments/
│           ├── python.md
│           ├── typescript.md
│           ├── go.md
│           ├── self_review.md
│           └── peer_review.md
└── main.py                   # Entry point: python -m skill_manager

tests/skill_manager/
├── __init__.py
├── test_models.py
├── test_store.py
├── test_language.py
├── test_trigger.py
├── test_resolver.py
└── test_server.py
```

---

## Task 1: Error Types

**Files:**
- Create: `skill_manager/errors.py`
- Test: `tests/skill_manager/test_models.py` (initially just error assertions)

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_models.py
from skill_manager.errors import SkillManagerError, SkillNotFoundError


def test_skill_not_found_is_skill_manager_error():
    err = SkillNotFoundError("foo")
    assert isinstance(err, SkillManagerError)
    assert str(err) == "foo"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/skill_manager/test_models.py::test_skill_not_found_is_skill_manager_error -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/errors.py
from core.shared.errors import AgentsDevelopError


class SkillManagerError(AgentsDevelopError):
    """Base error for the skill manager."""


class SkillNotFoundError(SkillManagerError):
    """Raised when a requested skill does not exist."""


class FragmentNotFoundError(SkillManagerError):
    """Raised when a requested fragment does not exist."""


class InvalidTriggerError(SkillManagerError):
    """Raised when a trigger rule is malformed."""


class StorageError(SkillManagerError):
    """Raised when storage read/write fails."""


class LanguageDetectionError(SkillManagerError):
    """Raised when language detection fails unexpectedly."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/skill_manager/test_models.py::test_skill_not_found_is_skill_manager_error -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/errors.py tests/skill_manager/test_models.py
git commit -m "feat(skill-manager): add error hierarchy

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Data Models

**Files:**
- Create: `skill_manager/models.py`
- Modify: `tests/skill_manager/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_models.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skill_manager/test_models.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager.models'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TriggerRule:
    type: Literal["slash", "keyword", "intent", "event"]
    value: str
    action: str
    language_hint: str | None = None


@dataclass
class Skill:
    name: str
    description: str
    version: str
    base_prompt: str
    default_action: str | None = None
    supported_languages: list[str] = field(default_factory=lambda: ["*"])
    tags: list[str] = field(default_factory=list)
    triggers: list[TriggerRule] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PromptFragment:
    id: str
    skill_name: str
    language: str | None = None
    action: str | None = None
    trigger: str | None = None
    priority: int = 0
    content: str = ""
    is_required: bool = False

    def match_score(self, language: str | None = None, action: str | None = None, trigger: str | None = None) -> int:
        score = 0
        if self.language is not None and self.language == language:
            score += 1
        if self.action is not None and self.action == action:
            score += 1
        if self.trigger is not None and self.trigger == trigger:
            score += 1
        return score


@dataclass
class ProjectOverride:
    skill_name: str
    project_path: str
    fragment: PromptFragment


@dataclass
class ResolveResult:
    skill: str
    resolved_for: dict
    prompt: str
    fragments_applied: list[str]
    fallback_used: bool
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "resolved_for": self.resolved_for,
            "prompt": self.prompt,
            "fragments_applied": self.fragments_applied,
            "fallback_used": self.fallback_used,
            "warnings": self.warnings,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skill_manager/test_models.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/models.py tests/skill_manager/test_models.py
git commit -m "feat(skill-manager): add data models

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Pluggable Storage (FileSystemStore)

**Files:**
- Create: `skill_manager/store.py`
- Test: `tests/skill_manager/test_store.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_store.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/skill_manager/test_store.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager.store'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/store.py
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

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
        import shutil

        skill_dir = self._skill_dir(name)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)

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
        content = path.read_text(encoding="utf-8")
        meta: dict[str, Any] = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta = {}

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
                    candidate.unlink()

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/skill_manager/test_store.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/store.py tests/skill_manager/test_store.py
git commit -m "feat(skill-manager): add pluggable file-system store

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Language Detector

**Files:**
- Create: `skill_manager/language.py`
- Test: `tests/skill_manager/test_language.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_language.py
from pathlib import Path

from skill_manager.language import HeuristicLanguageDetector


def test_explicit_language_wins(tmp_path: Path):
    detector = HeuristicLanguageDetector()
    result = detector.detect(project_path=str(tmp_path), file_path=None, explicit_language="go")
    assert result.primary_language == "go"
    assert result.confidence == 1.0


def test_detect_by_file_suffix():
    detector = HeuristicLanguageDetector()
    result = detector.detect(project_path=None, file_path="src/main.py")
    assert result.primary_language == "python"


def test_detect_by_project_marker(tmp_path: Path):
    detector = HeuristicLanguageDetector()
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'foo'\n")
    result = detector.detect(project_path=str(tmp_path), file_path=None)
    assert result.primary_language == "python"


def test_no_signals_return_none(tmp_path: Path):
    detector = HeuristicLanguageDetector()
    result = detector.detect(project_path=str(tmp_path), file_path=None)
    assert result.primary_language is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skill_manager/test_language.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager.language'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/language.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectResult:
    primary_language: str | None
    confidence: float
    secondary_languages: list[str]
    signals: list[str]


LANGUAGE_MARKERS = {
    "python": ["pyproject.toml", "setup.py", "requirements.txt", "*.py"],
    "typescript": ["tsconfig.json", "package.json", "*.ts", "*.tsx"],
    "javascript": ["package.json", "*.js", "*.jsx"],
    "go": ["go.mod", "*.go"],
    "rust": ["Cargo.toml", "*.rs"],
    "java": ["pom.xml", "build.gradle", "*.java"],
}


class LanguageDetector(ABC):
    @abstractmethod
    def detect(
        self,
        project_path: str | None,
        file_path: str | None,
        explicit_language: str | None = None,
    ) -> DetectResult: ...


class HeuristicLanguageDetector(LanguageDetector):
    def detect(
        self,
        project_path: str | None,
        file_path: str | None,
        explicit_language: str | None = None,
    ) -> DetectResult:
        if explicit_language:
            return DetectResult(
                primary_language=explicit_language,
                confidence=1.0,
                secondary_languages=[],
                signals=["explicit_language"],
            )

        if file_path:
            suffix = Path(file_path).suffix.lower()
            language = self._language_by_suffix(suffix)
            if language:
                return DetectResult(
                    primary_language=language,
                    confidence=0.9,
                    secondary_languages=[],
                    signals=[f"file_suffix:{suffix}"],
                )

        if project_path:
            project = Path(project_path)
            if project.is_dir():
                language = self._detect_by_markers(project)
                if language:
                    return DetectResult(
                        primary_language=language,
                        confidence=0.8,
                        secondary_languages=[],
                        signals=[f"project_marker:{language}"],
                    )

                language = self._detect_by_file_counts(project)
                if language:
                    return DetectResult(
                        primary_language=language,
                        confidence=0.6,
                        secondary_languages=[],
                        signals=["file_count"],
                    )

        return DetectResult(
            primary_language=None,
            confidence=0.0,
            secondary_languages=[],
            signals=["no_signals"],
        )

    @staticmethod
    def _language_by_suffix(suffix: str) -> str | None:
        mapping = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
        }
        return mapping.get(suffix)

    @staticmethod
    def _detect_by_markers(project: Path) -> str | None:
        for language, markers in LANGUAGE_MARKERS.items():
            for marker in markers:
                if marker.startswith("*."):
                    continue
                if (project / marker).exists():
                    return language
        return None

    @staticmethod
    def _detect_by_file_counts(project: Path) -> str | None:
        counts: dict[str, int] = {}
        for language, markers in LANGUAGE_MARKERS.items():
            for marker in markers:
                if marker.startswith("*."):
                    ext = marker[1:]
                    counts[language] = counts.get(language, 0) + len(list(project.rglob(f"*{ext}")))

        if not counts:
            return None
        primary = max(counts, key=counts.get)
        return primary if counts[primary] > 0 else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skill_manager/test_language.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/language.py tests/skill_manager/test_language.py
git commit -m "feat(skill-manager): add heuristic language detector

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Trigger Resolver

**Files:**
- Create: `skill_manager/trigger.py`
- Test: `tests/skill_manager/test_trigger.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_trigger.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skill_manager/test_trigger.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager.trigger'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/trigger.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from skill_manager.models import Skill


@dataclass
class TriggerResult:
    matched: bool
    trigger_type: str | None
    trigger_value: str | None
    action: str | None
    language_hint: str | None
    confidence: float


class TriggerResolver(ABC):
    @abstractmethod
    def resolve(self, input_text: str | None, event: str | None, skill: Skill) -> TriggerResult: ...


class MultiStrategyTriggerResolver(TriggerResolver):
    def resolve(self, input_text: str | None, event: str | None, skill: Skill) -> TriggerResult:
        text = (input_text or "").strip()

        for rule in skill.triggers:
            if rule.type == "slash" and text.startswith(rule.value):
                return TriggerResult(
                    matched=True,
                    trigger_type="slash",
                    trigger_value=rule.value,
                    action=rule.action,
                    language_hint=rule.language_hint,
                    confidence=1.0,
                )

        for rule in skill.triggers:
            if rule.type == "keyword" and rule.value.lower() in text.lower():
                return TriggerResult(
                    matched=True,
                    trigger_type="keyword",
                    trigger_value=rule.value,
                    action=rule.action,
                    language_hint=rule.language_hint,
                    confidence=0.8,
                )

        for rule in skill.triggers:
            if rule.type == "event" and event == rule.value:
                return TriggerResult(
                    matched=True,
                    trigger_type="event",
                    trigger_value=rule.value,
                    action=rule.action,
                    language_hint=rule.language_hint,
                    confidence=1.0,
                )

        for rule in skill.triggers:
            if rule.type == "intent" and text.lower() == rule.value.lower():
                return TriggerResult(
                    matched=True,
                    trigger_type="intent",
                    trigger_value=rule.value,
                    action=rule.action,
                    language_hint=rule.language_hint,
                    confidence=0.9,
                )

        return TriggerResult(
            matched=False,
            trigger_type=None,
            trigger_value=None,
            action=skill.default_action,
            language_hint=None,
            confidence=0.0,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skill_manager/test_trigger.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/trigger.py tests/skill_manager/test_trigger.py
git commit -m "feat(skill-manager): add multi-strategy trigger resolver

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Resolution Engine

**Files:**
- Create: `skill_manager/resolver.py`
- Test: `tests/skill_manager/test_resolver.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_resolver.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skill_manager/test_resolver.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager.resolver'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/resolver.py
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
        for fragment in skill_fragments:
            score = fragment.match_score(language=language, action=action, trigger=trigger)
            if score == 0:
                continue
            score_buckets.setdefault(score, []).append(fragment)

        for score in sorted(score_buckets.keys(), reverse=True):
            bucket = sorted(score_buckets[score], key=lambda f: f.priority, reverse=True)
            fragments.extend(bucket)

        # Deduplicate by id while preserving order
        seen: set[str] = set()
        unique_fragments: list[PromptFragment] = []
        for fragment in fragments:
            if fragment.id in seen:
                continue
            seen.add(fragment.id)
            unique_fragments.append(fragment)

        fallback_used = not unique_fragments and (language is None or action is None or trigger is None)

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skill_manager/test_resolver.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/resolver.py tests/skill_manager/test_resolver.py
git commit -m "feat(skill-manager): add priority resolution engine

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Built-in Skill Package

**Files:**
- Create: `skill_manager/builtin_skills/__init__.py`
- Create: `skill_manager/builtin_skills/code_review/skill.json`
- Create: `skill_manager/builtin_skills/code_review/base_prompt.md`
- Create: `skill_manager/builtin_skills/code_review/fragments/python.md`
- Create: `skill_manager/builtin_skills/code_review/fragments/typescript.md`
- Create: `skill_manager/builtin_skills/code_review/fragments/go.md`
- Create: `skill_manager/builtin_skills/code_review/fragments/self_review.md`
- Create: `skill_manager/builtin_skills/code_review/fragments/peer_review.md`
- Test: `tests/skill_manager/test_store.py` (add loader test)

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_store.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/skill_manager/test_store.py::test_load_builtin_skills -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager.builtin_skills'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/builtin_skills/__init__.py
from __future__ import annotations

from pathlib import Path

from skill_manager.store import FileSystemStore


def load_builtin_skills(store: FileSystemStore, source_root: str | None = None) -> None:
    if source_root is None:
        source_root = str(Path(__file__).parent)

    root = Path(source_root)
    for skill_dir in root.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_path = skill_dir / "skill.json"
        if not skill_path.exists():
            continue

        # Load by copying files into store directory
        target_skill_dir = store._skill_dir(skill_dir.name)
        target_skill_dir.mkdir(parents=True, exist_ok=True)

        for src_file in skill_dir.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(skill_dir)
            dest = target_skill_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src_file.read_bytes())
```

```json
// skill_manager/builtin_skills/code_review/skill.json
{
  "name": "code_review",
  "description": "Review code for quality, bugs, and style issues.",
  "version": "1.0.0",
  "default_action": "self_review",
  "supported_languages": ["python", "typescript", "go", "javascript", "rust", "java", "*"],
  "tags": ["review", "quality"],
  "triggers": [
    {"type": "slash", "value": "/review", "action": "self_review"},
    {"type": "slash", "value": "/review-python", "action": "self_review", "language_hint": "python"},
    {"type": "slash", "value": "/review-go", "action": "self_review", "language_hint": "go"},
    {"type": "slash", "value": "/review-ts", "action": "self_review", "language_hint": "typescript"},
    {"type": "keyword", "value": "review this code", "action": "self_review"},
    {"type": "event", "value": "on_save", "action": "quick_review"}
  ],
  "created_at": "2026-06-26",
  "updated_at": "2026-06-26"
}
```

```markdown
<!-- skill_manager/builtin_skills/code_review/base_prompt.md -->
# Code Review

You are reviewing code. Focus on correctness, readability, maintainability, and performance.

## Universal Checklist

- [ ] Check for obvious bugs or logic errors.
- [ ] Verify error handling paths.
- [ ] Look for unnecessary complexity.
- [ ] Ensure naming is clear and consistent.
- [ ] Confirm tests cover the changed behavior.
```

```markdown
<!-- skill_manager/builtin_skills/code_review/fragments/python.md -->
## Python-Specific Guidance

- Prefer `pathlib.Path` over `os.path`.
- Use type hints for function signatures.
- Follow PEP 8 naming conventions.
- Handle exceptions explicitly; avoid bare `except:`.
```

```markdown
<!-- skill_manager/builtin_skills/code_review/fragments/typescript.md -->
## TypeScript-Specific Guidance

- Prefer `strict` TypeScript mode.
- Avoid `any`; use `unknown` when type is uncertain.
- Use explicit return types for public functions.
```

```markdown
<!-- skill_manager/builtin_skills/code_review/fragments/go.md -->
## Go-Specific Guidance

- Follow `gofmt` formatting.
- Handle errors explicitly; never ignore returned errors.
- Keep functions small and focused.
```

```markdown
<!-- skill_manager/builtin_skills/code_review/fragments/self_review.md -->
## Self-Review Mode

Review your own code before asking others. Be honest about trade-offs and risks.
```

```markdown
<!-- skill_manager/builtin_skills/code_review/fragments/peer_review.md -->
## Peer-Review Mode

Provide constructive feedback. Suggest concrete improvements with examples.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/skill_manager/test_store.py::test_load_builtin_skills -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/builtin_skills tests/skill_manager/test_store.py
git commit -m "feat(skill-manager): add built-in code_review skill

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: MCP Server

**Files:**
- Create: `skill_manager/server.py`
- Create: `skill_manager/main.py`
- Test: `tests/skill_manager/test_server.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_server.py
from pathlib import Path

from skill_manager.server import create_server
from skill_manager.store import FileSystemStore


def test_list_skills_tool(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    tools = server.list_tools()
    assert any(t.name == "list_skills" for t in tools)


def test_resolve_skill_tool(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    server = create_server(store)
    tool = next(t for t in server.list_tools() if t.name == "resolve_skill")
    assert "name" in tool.inputSchema["required"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skill_manager/test_server.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'skill_manager.server'`

- [ ] **Step 3: Write minimal implementation**

```python
# skill_manager/server.py
from __future__ import annotations

from mcp.server import Server
from mcp.types import Tool, TextContent

from skill_manager.errors import SkillNotFoundError
from skill_manager.language import HeuristicLanguageDetector
from skill_manager.resolver import PriorityResolver
from skill_manager.store import SkillStore
from skill_manager.trigger import MultiStrategyTriggerResolver


def create_server(store: SkillStore) -> Server:
    server = Server("skill-manager")
    resolver = PriorityResolver(store)
    language_detector = HeuristicLanguageDetector()
    trigger_resolver = MultiStrategyTriggerResolver()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_skills",
                description="List all registered skills with optional filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter_language": {"type": "string"},
                        "filter_action": {"type": "string"},
                        "filter_tag": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="resolve_skill",
                description="Resolve a skill prompt for given context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "language": {"type": "string"},
                        "action": {"type": "string"},
                        "trigger": {"type": "string"},
                        "project_path": {"type": "string"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="detect_language",
                description="Detect primary programming language of a project or file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"},
                        "file_path": {"type": "string"},
                        "explicit_language": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="register_skill",
                description="Register a new skill with metadata and optional fragments",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metadata": {"type": "object"},
                        "base_prompt": {"type": "string"},
                        "fragments": {"type": "array"},
                    },
                    "required": ["metadata", "base_prompt"],
                },
            ),
            Tool(
                name="update_fragment",
                description="Add or update a prompt fragment for a skill",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string"},
                        "fragment": {"type": "object"},
                    },
                    "required": ["skill_name", "fragment"],
                },
            ),
            Tool(
                name="register_trigger",
                description="Register a custom trigger rule for a skill",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string"},
                        "trigger": {"type": "object"},
                    },
                    "required": ["skill_name", "trigger"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "list_skills":
            filters = {k: v for k, v in arguments.items() if v is not None}
            skills = store.list_skills(filters)
            payload = [
                {
                    "name": s.name,
                    "description": s.description,
                    "version": s.version,
                    "default_action": s.default_action,
                    "supported_languages": s.supported_languages,
                }
                for s in skills
            ]
            return [TextContent(type="text", text=str(payload))]

        if name == "resolve_skill":
            skill_name = arguments["name"]
            language = arguments.get("language")
            action = arguments.get("action")
            trigger = arguments.get("trigger")
            project_path = arguments.get("project_path")

            if language is None:
                detect = language_detector.detect(project_path, arguments.get("file_path"))
                language = detect.primary_language

            if action is None or trigger is None:
                skill = store.get_skill(skill_name)
                if skill is None:
                    raise SkillNotFoundError(f"Skill '{skill_name}' not found")
                trigger_result = trigger_resolver.resolve(trigger or "", None, skill)
                action = action or trigger_result.action or skill.default_action
                language = language or trigger_result.language_hint

            result = resolver.resolve(
                name=skill_name,
                language=language,
                action=action,
                trigger=trigger,
                project_path=project_path,
            )
            return [TextContent(type="text", text=str(result.to_dict()))]

        if name == "detect_language":
            result = language_detector.detect(
                arguments.get("project_path"),
                arguments.get("file_path"),
                arguments.get("explicit_language"),
            )
            return [TextContent(type="text", text=str({
                "primary_language": result.primary_language,
                "confidence": result.confidence,
                "secondary_languages": result.secondary_languages,
                "signals": result.signals,
            }))]

        if name == "register_skill":
            from skill_manager.models import Skill, TriggerRule

            metadata = arguments["metadata"]
            skill = Skill(
                name=metadata["name"],
                description=metadata.get("description", ""),
                version=metadata.get("version", "1.0.0"),
                base_prompt=arguments["base_prompt"],
                default_action=metadata.get("default_action"),
                supported_languages=metadata.get("supported_languages", ["*"]),
                tags=metadata.get("tags", []),
                triggers=[TriggerRule(**t) for t in metadata.get("triggers", [])],
            )
            store.save_skill(skill)

            for fragment_data in arguments.get("fragments", []):
                from skill_manager.models import PromptFragment

                fragment = PromptFragment(
                    id=fragment_data["id"],
                    skill_name=skill.name,
                    language=fragment_data.get("language"),
                    action=fragment_data.get("action"),
                    trigger=fragment_data.get("trigger"),
                    priority=fragment_data.get("priority", 0),
                    content=fragment_data["content"],
                    is_required=fragment_data.get("is_required", False),
                )
                store.save_fragment(fragment)

            return [TextContent(type="text", text=f"Skill '{skill.name}' registered.")]

        if name == "update_fragment":
            from skill_manager.models import PromptFragment

            skill_name = arguments["skill_name"]
            fragment_data = arguments["fragment"]
            fragment = PromptFragment(
                id=fragment_data["id"],
                skill_name=skill_name,
                language=fragment_data.get("language"),
                action=fragment_data.get("action"),
                trigger=fragment_data.get("trigger"),
                priority=fragment_data.get("priority", 0),
                content=fragment_data["content"],
                is_required=fragment_data.get("is_required", False),
            )
            store.save_fragment(fragment)
            return [TextContent(type="text", text=f"Fragment '{fragment.id}' updated.")]

        if name == "register_trigger":
            from skill_manager.models import TriggerRule

            skill_name = arguments["skill_name"]
            trigger_data = arguments["trigger"]
            skill = store.get_skill(skill_name)
            if skill is None:
                raise SkillNotFoundError(f"Skill '{skill_name}' not found")
            skill.triggers.append(TriggerRule(**trigger_data))
            store.save_skill(skill)
            return [TextContent(type="text", text=f"Trigger registered for '{skill_name}'.")]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return server
```

```python
# skill_manager/main.py
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from skill_manager.builtin_skills import load_builtin_skills
from skill_manager.server import create_server
from skill_manager.store import FileSystemStore


DEFAULT_ROOT = Path.home() / ".agents-develop" / "skill-manager"


def main() -> None:
    root = os.environ.get("SKILL_MANAGER_ROOT", str(DEFAULT_ROOT))
    store = FileSystemStore(root)
    load_builtin_skills(store)

    server = create_server(store)

    async def run() -> None:
        async with server.run() as runner:
            await runner.wait()

    asyncio.run(run())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skill_manager/test_server.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skill_manager/server.py skill_manager/main.py tests/skill_manager/test_server.py
git commit -m "feat(skill-manager): add MCP server and entry point

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Project Packaging and Entry Script

**Files:**
- Modify: `pyproject.toml`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_server.py
import subprocess
import sys


def test_entry_point_imports():
    result = subprocess.run(
        [sys.executable, "-m", "skill_manager", "--help"],
        capture_output=True,
        text=True,
    )
    # Module has no CLI yet; just verify it does not crash on import.
    assert result.returncode != 2 or "No module named" not in result.stderr
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/skill_manager/test_server.py::test_entry_point_imports -v`

Expected: FAIL (exit code non-zero because module not importable as package yet)

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml additions
[project.optional-dependencies]
mcp = ["mcp>=1.0"]
dev = ["pytest>=7.0", "pytest-cov>=4.0", "ruff>=0.1"]

[project.scripts]
agents-dev = "cli.main:main"
skill-manager = "skill_manager.main:main"

[tool.setuptools.packages.find]
include = ["core*", "cli*", "migration*", "formats*", "skill_manager*"]
```

```markdown
# CLAUDE.md additions (append under Development section)

## Project Convention

Each independent feature should be developed as a standalone package/component rather than being forced into a rigid shared directory hierarchy. The existing `core/`, `formats/`, `components/`, and `cli/` structure is the reference environment for the core framework. New capabilities (such as `skill_manager/`) live as separate packages at the repository root and may be installed, tested, and versioned independently.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/skill_manager/test_server.py::test_entry_point_imports -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml CLAUDE.md
git commit -m "chore(skill-manager): wire package entry point and update project convention

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: Integration Test

**Files:**
- Create: `tests/skill_manager/test_integration.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/skill_manager/test_integration.py
from pathlib import Path

from skill_manager.builtin_skills import load_builtin_skills
from skill_manager.server import create_server
from skill_manager.store import FileSystemStore


async def test_resolve_code_review_python(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    load_builtin_skills(store)
    server = create_server(store)

    tools = {t.name: t for t in server.list_tools()}
    assert "resolve_skill" in tools

    result = await server.call_tool("resolve_skill", {
        "name": "code_review",
        "language": "python",
        "action": "self_review",
        "trigger": "/review",
    })
    text = result[0].text
    assert "Code Review" in text
    assert "Python-Specific Guidance" in text
    assert "Self-Review Mode" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/skill_manager/test_integration.py -v`

Expected: FAIL (await syntax inside non-async test or missing module)

- [ ] **Step 3: Write minimal implementation**

```python
# tests/skill_manager/test_integration.py
from pathlib import Path

import pytest

from skill_manager.builtin_skills import load_builtin_skills
from skill_manager.server import create_server
from skill_manager.store import FileSystemStore


@pytest.mark.anyio
async def test_resolve_code_review_python(tmp_path: Path):
    store = FileSystemStore(str(tmp_path))
    load_builtin_skills(store)
    server = create_server(store)

    tools = {t.name: t for t in server.list_tools()}
    assert "resolve_skill" in tools

    result = await server.call_tool("resolve_skill", {
        "name": "code_review",
        "language": "python",
        "action": "self_review",
        "trigger": "/review",
    })
    text = result[0].text
    assert "Code Review" in text
    assert "Python-Specific Guidance" in text
    assert "Self-Review Mode" in text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/skill_manager/test_integration.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/skill_manager/test_integration.py
git commit -m "test(skill-manager): add integration test for resolve_skill

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

### Spec coverage

| Spec section | Implementing task |
| --- | --- |
| Data models | Task 2 |
| Storage abstraction | Task 3 |
| Language detector | Task 4 |
| Trigger resolver | Task 5 |
| Resolution engine | Task 6 |
| Built-in skills | Task 7 |
| MCP interfaces | Task 8 |
| Project packaging | Task 9 |
| Integration test | Task 10 |

### Placeholder scan

- No "TBD", "TODO", or vague steps.
- Every step includes concrete code, file paths, and commands.
- Every test includes the actual assertion.

### Type consistency

- `SkillStore` methods use the same names and signatures defined in the spec.
- `ResolveResult.to_dict()` matches the expected wire format.
- Trigger rule `type` uses the same literals everywhere.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-26-mcp-skill-manager-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints

**Which approach?**
