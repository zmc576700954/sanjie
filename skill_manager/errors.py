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
