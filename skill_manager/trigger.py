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
