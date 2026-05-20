"""Tests for the scope guardian (sanjian skill)."""

from skills.tool_sanjian.scripts.scope_guardian import check_scope, SCOPE_HIERARCHY


class TestCheckScope:
    def test_safe_within_safe(self):
        """SAFE subtask with SAFE current scope should PROCEED."""
        subtask = {"id": "t1", "target_file": "a.py", "operation": "REWRITE", "scope_level": "SAFE"}
        result = check_scope(subtask, current_scope="SAFE")
        assert result["approved"] is True
        assert result["action"] == "PROCEED"

    def test_safe_within_boundary(self):
        """SAFE subtask with BOUNDARY authorization should PROCEED."""
        subtask = {"id": "t1", "scope_level": "SAFE"}
        result = check_scope(subtask, current_scope="BOUNDARY")
        assert result["approved"] is True
        assert result["action"] == "PROCEED"

    def test_boundary_within_boundary(self):
        """BOUNDARY subtask with BOUNDARY authorization should PROCEED."""
        subtask = {"id": "t1", "scope_level": "BOUNDARY"}
        result = check_scope(subtask, current_scope="BOUNDARY")
        assert result["approved"] is True
        assert result["action"] == "PROCEED"

    def test_deep_requires_approval(self):
        """DEEP subtask with SAFE authorization should HALT."""
        subtask = {"id": "t1", "scope_level": "DEEP"}
        result = check_scope(subtask, current_scope="SAFE")
        assert result["approved"] is False
        assert result["action"] == "HALT"
        assert result.get("approval_required") is True

    def test_deep_with_auto_approve(self):
        """DEEP subtask with auto_approve=True should EXPAND."""
        subtask = {"id": "t1", "scope_level": "DEEP"}
        result = check_scope(subtask, current_scope="SAFE", auto_approve=True)
        assert result["approved"] is True
        assert result["action"] == "EXPAND"
        assert result["authorized_scope"] == "DEEP"

    def test_boundary_with_auto_approve(self):
        """BOUNDARY subtask with auto_approve=True should EXPAND."""
        subtask = {"id": "t1", "scope_level": "BOUNDARY"}
        result = check_scope(subtask, current_scope="SAFE", auto_approve=True)
        assert result["approved"] is True
        assert result["action"] == "EXPAND"
        assert result["authorized_scope"] == "BOUNDARY"

    def test_scope_hierarchy_order(self):
        """SCOPE_HIERARCHY must have SAFE < BOUNDARY < DEEP."""
        assert SCOPE_HIERARCHY["SAFE"] < SCOPE_HIERARCHY["BOUNDARY"]
        assert SCOPE_HIERARCHY["BOUNDARY"] < SCOPE_HIERARCHY["DEEP"]

    def test_default_scope_is_safe(self):
        """When no current_scope provided, default should be SAFE."""
        subtask = {"id": "t1", "scope_level": "SAFE"}
        result = check_scope(subtask)
        assert result["approved"] is True
        assert result["action"] == "PROCEED"
        assert result["authorized_scope"] == "SAFE"

    def test_deep_fails_without_auto_approve(self):
        """DEEP subtask without auto_approve should return HALT with message."""
        subtask = {"id": "t1", "scope_level": "DEEP"}
        result = check_scope(subtask, current_scope="SAFE")
        assert result["approved"] is False
        assert result["action"] == "HALT"
        assert "Scope expansion needed" in result.get("message", "")
