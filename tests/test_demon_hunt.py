from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.demon_hunt import demon_hunt


class TestDemonHuntBusinessHead:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_business_head_returns_findings(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"findings": [{"id": "B001", "severity": "high", "description": "Business rule violation", "scenario": "edge case"}], '
            '"confidence": "high"}'
        )
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="payment.py",
            mode="code_review",
            head_type="business",
            context="",
        )

        assert "[task_status]: completed" in result
        assert "[demon_hunt_result]: head_type=business" in result
        assert "[findings]" in result
        assert "Business rule violation" in result
        assert "[next_action]" in result
        mock_provider.infer.assert_called_once()


class TestDemonHuntCodeHead:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_code_head_returns_findings(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"findings": [{"id": "C001", "severity": "critical", "category": "null_pointer", "description": "Null risk", "pattern": "missing check"}], '
            '"confidence": "high"}'
        )
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            head_type="code",
            context="",
        )

        assert "[task_status]: completed" in result
        assert "[demon_hunt_result]: head_type=code" in result
        assert "[findings]" in result
        assert "Null risk" in result
        mock_provider.infer.assert_called_once()


class TestDemonHuntCognitiveHead:
    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_cognitive_head_returns_full_report(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"root_causes": [{"id": "RC001", "confidence": "high", "description": "Root cause found", "evidence": "line 42", "surface_symptom": "crash", "true_nature": "missing validation"}], '
            '"business_risks": [{"id": "BR001", "severity": "high", "description": "Business violation"}], '
            '"code_risks": [{"id": "CR001", "severity": "critical", "category": "null_pointer", "description": "Null risk"}], '
            '"suggested_fixes": [{"id": "SF001", "priority": "P0", "description": "Fix validation", "files_affected": ["core.py"]}]}'
        )
        mock_get_provider.return_value = mock_provider

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            head_type="cognitive",
            context="YangJian report: possible race condition",
        )

        assert "[task_status]: completed" in result
        assert "[demon_hunt_result]: head_type=cognitive" in result
        assert "[root_cause]" in result
        assert "[business_risk]" in result
        assert "[code_risk]" in result
        assert "[suggested_fixes]" in result
        assert "Root cause found" in result
        assert "[persona_handoff]" in result
        mock_provider.infer.assert_called_once()

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_cognitive_head_no_provider_fallback(self, mock_get_provider):
        mock_get_provider.return_value = None

        result = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            head_type="cognitive",
        )

        assert "[task_status]: completed" in result
        assert "[demon_hunt_result]: head_type=cognitive" in result
        assert "Fallback" in result
