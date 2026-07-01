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
