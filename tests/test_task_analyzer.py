"""Tests for the task analyzer (bajiu skill)."""

from skills.tool_bajiu.scripts.task_analyzer import analyze_task, route_task


class TestAnalyzeTask:
    def test_trivial_fix(self):
        """Small-scope fix task with yindan profile should match TRIVIAL."""
        profiles = [
            {"name": "yindan", "description": "Precision fix", "tools": ["precise_fix"]},
        ]
        result = analyze_task("Fix a null pointer error in this file", profiles)
        assert result["difficulty"] == "TRIVIAL"
        assert len(result["matched_candidates"]) >= 1
        assert "yindan" in result["matched_candidates"][0]["name"]

    def test_feature_development_with_profiles(self):
        """Feature request should match taie when profile is available."""
        profiles = [
            {"name": "yindan", "description": "Precision fix", "tools": ["precise_fix"]},
            {"name": "taie", "description": "Feature development", "tools": ["standard_write"]},
        ]
        result = analyze_task("implement new payment feature", profiles)
        assert result["difficulty"] == "MODERATE"
        assert len(result["matched_candidates"]) >= 1
        assert "taie" in result["matched_candidates"][0]["name"]

    def test_refactor_task(self):
        """Refactor request should match sanjian when scope is large."""
        profiles = [
            {"name": "yindan", "description": "Precision fix", "tools": ["precise_fix"]},
            {"name": "sanjian", "description": "Multi-file refactoring", "tools": ["executor"]},
        ]
        result = analyze_task("refactor this multi-file module structure", profiles)
        assert result["difficulty"] == "COMPLEX"
        assert len(result["matched_candidates"]) >= 1
        assert "sanjian" in result["matched_candidates"][0]["name"]

    def test_bulk_cleanup(self):
        """Bulk cleanup with global scope should match kaishan."""
        profiles = [
            {"name": "kaishan", "description": "Bulk operations", "tools": ["bulk_operations"]},
        ]
        # "global" triggers scope=1.0, which passes kaishan's prerequisite (scope >= 0.4)
        result = analyze_task("global delete of deprecated test files", profiles)
        assert result["difficulty"] == "CRITICAL"
        assert len(result["matched_candidates"]) >= 1
        assert "kaishan" in result["matched_candidates"][0]["name"]

    def test_unknown_task(self):
        """Unknown task should yield UNDETERMINED."""
        profiles = [
            {"name": "yindan", "description": "Fix", "tools": ["precise_fix"]},
            {"name": "taie", "description": "Feature", "tools": ["standard_write"]},
        ]
        result = analyze_task("something completely unrelated xyz123", profiles)
        # No skill should pass prerequisites for an unrelated task
        assert result["matched_candidates"] == []

    def test_extracted_factors(self):
        """Task analysis should extract the correct decision factors."""
        result = analyze_task("fix a bug in this file", [])
        factors = result["factors"]
        assert factors["is_fix"] is True
        assert factors["is_create"] is False
        assert factors["scope"] <= 0.3  # single file scope


class TestRouteTask:
    def test_route_with_recommendation(self):
        """Handoff with [recommended_skill] should use that recommendation."""
        context = "Some analysis\n[recommended_skill]: yindan\nMore text"
        result = route_task(context, "TRIVIAL", [])
        assert result["execution_plan"][0]["skill"] == "yindan"

    def test_route_with_best_match(self):
        """Without recommendation, route to best matched candidate."""
        candidates = [{"name": "taie", "reason": "Feature development", "score": 0.8}]
        result = route_task("implement feature", "MODERATE", candidates)
        assert result["execution_plan"][0]["skill"] == "taie"

    def test_route_no_match(self):
        """No candidates should yield 'none' as the skill."""
        result = route_task("unknown task", "UNDETERMINED", [])
        assert result["execution_plan"][0]["skill"] == "none"
        assert "No skill matched" in result["execution_plan"][0]["action"]
