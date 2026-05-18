import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from skills.tool_bajiu.scripts.keyword_router import classify_error
from skills.tool_bajiu.scripts.confidence_scorer import score_classification
from skills.tool_bajiu.scripts.environment_probe import detect_host_environment


def test_classify_none_error():
    result = classify_error("NoneType has no attribute 'foo'")
    assert result["recommended_skill"] == "yindan"


def test_classify_refactor():
    result = classify_error("Need to refactor this module")
    assert result["recommended_skill"] == "sanjian"


def test_classify_bulk_cleanup():
    result = classify_error("bulk cleanup of deprecated code")
    assert result["recommended_skill"] == "kaishan"


def test_classify_feature():
    result = classify_error("implement new payment feature")
    assert result["recommended_skill"] == "taie"


def test_classify_import_error():
    result = classify_error("ImportError: No module named 'missing'")
    assert result["recommended_skill"] == "yindan"


def test_classify_unknown():
    result = classify_error("something weird happened")
    assert result["recommended_skill"] == "yindan"
    assert "Insufficient information" in result["root_cause"]


def test_high_confidence_single_match():
    result = {"recommended_skill": "yindan"}
    assert score_classification(result, "NoneType error") >= 0.7


def test_low_confidence_ambiguous():
    result = {"recommended_skill": "yindan"}
    assert score_classification(result, "something weird happened") == 0.5


def test_detect_host_returns_structure():
    env = detect_host_environment()
    assert "host" in env
    assert "has_ollama" in env
    assert "has_api_key" in env
    assert "available_providers" in env
    assert env["host"] in ["claude_code", "cursor", "gemini_cli", "codex", "trae", "none"]
