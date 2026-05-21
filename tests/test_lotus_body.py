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


class TestLotusBodySixArms:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_six_arms_trinity_mode(self, mock_get_provider):
        mock_provider = MagicMock()
        # 4 calls: assignment plan, main arms, left arms, right arms
        mock_provider.infer.side_effect = [
            # Main arms result (call 1)
            '{"execution_plan": [{"id": "EP-M1", "priority": "P0", "target_file": "core.py", "change_type": "fix", "description": "Fix core logic"}], "execution_result": [{"id": "EP-M1", "status": "success", "diff_summary": "Fixed core", "files_modified": ["core.py"]}]}',
            # Left arms result (call 2)
            '{"execution_plan": [{"id": "EP-L1", "priority": "P1", "target_file": "handlers.py", "change_type": "fix", "description": "Add boundary"}], "execution_result": [{"id": "EP-L1", "status": "success", "diff_summary": "Added boundary", "files_modified": ["handlers.py"]}]}',
            # Right arms result (call 3)
            '{"execution_plan": [{"id": "EP-R1", "priority": "P2", "target_file": "utils.py", "change_type": "optimize", "description": "Optimize imports"}], "execution_result": [{"id": "EP-R1", "status": "success", "diff_summary": "Optimized", "files_modified": ["utils.py"]}]}',
        ]
        mock_get_provider.return_value = mock_provider

        result = lotus_body(
            input_source="direct_instruction",
            input_payload={"instruction": "Major refactoring across 8 files"},
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="high",
        )

        assert "[lotus_report]" in result
        assert "trinity_six_arms" in result
        assert "main_arms" in result
        assert "left_arms" in result
        assert "right_arms" in result
        assert "core.py" in result
        assert "handlers.py" in result
        assert "utils.py" in result
        assert mock_provider.infer.call_count == 3

    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_six_arms_with_demon_hunt_report(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.side_effect = [
            '{"execution_plan": [], "execution_result": []}',
            '{"execution_plan": [], "execution_result": []}',
            '{"execution_plan": [], "execution_result": []}',
        ]
        mock_get_provider.return_value = mock_provider

        report = {
            "suggested_fixes": [
                {"id": "SF-001", "priority": "P0", "files_affected": ["a.py"], "description": "Fix race condition"},
            ]
        }
        result = lotus_body(
            input_source="demon_hunt_report",
            input_payload=report,
            file_count=6,
            line_change_est=300,
            complexity="complex",
            risk_level="critical",
        )

        assert "trinity_six_arms" in result
