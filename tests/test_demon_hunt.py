from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.demon_hunt import demon_hunt


class TestDemonHuntSingleHead:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_single_head_returns_report(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"root_causes": [{"id": "RC-001", "description": "Missing null check", "evidence": "line 42"}], '
            '"business_risks": [], "code_risks": [], '
            '"suggested_fixes": [{"id": "SF-001", "priority": "P0", "files_affected": ["core.py"], "description": "Add null check"}]}'
        )
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            file_count=1,
            line_change_est=20,
            complexity="simple",
            risk_level="low",
        )

        assert "[nezha_report]" in result
        assert "single_head" in result
        assert "[root_cause]" in result
        assert "Missing null check" in result
        mock_provider.infer.assert_called_once()

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_single_head_no_provider_fallback(self, mock_get_provider):
        mock_get_provider.return_value = None

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            file_count=1,
            line_change_est=20,
            complexity="simple",
            risk_level="low",
        )

        assert "[nezha_report]" in result
        assert "[root_cause]" in result
        assert "Fallback analysis" in result


class TestDemonHuntDualHead:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_dual_head_bug_hunt_calls_twice(self, mock_get_provider):
        mock_provider = MagicMock()
        # dual_head for bug_hunt: code_head + cognitive_head
        mock_provider.infer.side_effect = [
            '{"findings": [{"id": "C001", "severity": "critical", "category": "null_pointer", "description": "Null risk", "pattern": "missing check"}]}',
            '{"root_causes": [{"id": "RC001", "description": "Root found", "evidence": "line 42"}], "suggested_fixes": []}',
        ]
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="payment.py",
            mode="bug_hunt",
            file_count=3,
            line_change_est=100,
            complexity="moderate",
            risk_level="medium",
        )

        assert "[nezha_report]" in result
        assert "dual_head" in result
        assert "[code_risk]" in result
        assert "Null risk" in result
        assert mock_provider.infer.call_count == 2

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_dual_head_code_review_calls_business(self, mock_get_provider):
        mock_provider = MagicMock()
        # dual_head for code_review: business_head + cognitive_head
        mock_provider.infer.side_effect = [
            '{"findings": [{"id": "B001", "severity": "high", "description": "Business violation", "scenario": "edge"}]}',
            '{"root_causes": [{"id": "RC001", "description": "Root found"}], "suggested_fixes": []}',
        ]
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="payment.py",
            mode="code_review",
            file_count=3,
            line_change_est=100,
            complexity="moderate",
            risk_level="medium",
        )

        assert "[nezha_report]" in result
        assert "dual_head" in result
        assert "[business_risk]" in result
        assert "Business violation" in result
        assert mock_provider.infer.call_count == 2
