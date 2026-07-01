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
