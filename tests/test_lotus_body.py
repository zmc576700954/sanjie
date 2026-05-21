from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.lotus_body import lotus_body


class TestLotusBodySingleArms:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_single_arms_direct_instruction(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"execution_plan": [{"id": "EP-001", "priority": "P0", "target_file": "core.py", '
            '"line_range": "42-56", "change_type": "fix", "description": "Add null check"}], '
            '"execution_result": [{"id": "EP-001", "status": "success", "diff_summary": "Added null check", "files_modified": ["core.py"]}]}'
        )
        mock_get_provider.return_value = mock_provider

        result = lotus_body(
            input_source="direct_instruction",
            input_payload={"instruction": "Add null check to getBucket()"},
            file_count=1,
            line_change_est=10,
            complexity="simple",
            risk_level="low",
        )

        assert "[lotus_report]" in result
        assert "single_head" in result
        assert "[execution_plan]" in result
        assert "[execution_result]" in result
        mock_provider.infer.assert_called_once()

    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_single_arms_no_provider_fallback(self, mock_get_provider):
        mock_get_provider.return_value = None

        result = lotus_body(
            input_source="direct_instruction",
            input_payload={"instruction": "Fix typo"},
            file_count=1,
            line_change_est=5,
            complexity="simple",
            risk_level="low",
        )

        assert "[lotus_report]" in result
        assert "[execution_plan]" in result
        assert "Fallback execution" in result
