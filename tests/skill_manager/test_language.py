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
