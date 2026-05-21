from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.lotus_body import lotus_body


class TestLotusBodyMainArm:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_main_arm_execution(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"execution_plan": [{"id": "EP-M1", "priority": "P0", "target_file": "core.py", '
            '"line_range": "42-56", "change_type": "fix", "description": "Fix core logic"}], '
            '"execution_result": [{"id": "EP-M1", "status": "success", "diff_summary": "Fixed core", "files_modified": ["core.py"]}], '
            '"verification_checklist": ["[ ] Run tests"]}'
        )
        mock_get_provider.return_value = mock_provider

        result = lotus_body(
            task="Fix null check in getBucket()",
            arm_type="main",
            scope_limit=["core.py"],
            safety_level="standard",
        )

        assert "[task_status]: completed" in result
        assert "[lotus_body_result]: arm_type=main" in result
        assert "[execution_plan]" in result
        assert "[execution_result]" in result
        assert "Fix core logic" in result
        mock_provider.infer.assert_called_once()


class TestLotusBodyLeftArm:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_left_arm_execution(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"execution_plan": [{"id": "EP-L1", "priority": "P1", "target_file": "handlers.py", "change_type": "fix", "description": "Add boundary check"}], '
            '"execution_result": [{"id": "EP-L1", "status": "success", "diff_summary": "Added boundary", "files_modified": ["handlers.py"]}], '
            '"verification_checklist": []}'
        )
        mock_get_provider.return_value = mock_provider

        result = lotus_body(
            task="Add boundary handling",
            arm_type="left",
        )

        assert "[task_status]: completed" in result
        assert "[lotus_body_result]: arm_type=left" in result
        assert "Add boundary check" in result


class TestLotusBodyRightArm:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_right_arm_execution(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"execution_plan": [{"id": "EP-R1", "priority": "P2", "target_file": "utils.py", "change_type": "optimize", "description": "Optimize imports"}], '
            '"execution_result": [{"id": "EP-R1", "status": "success", "diff_summary": "Optimized", "files_modified": ["utils.py"]}], '
            '"verification_checklist": []}'
        )
        mock_get_provider.return_value = mock_provider

        result = lotus_body(
            task="Optimize code structure",
            arm_type="right",
        )

        assert "[task_status]: completed" in result
        assert "[lotus_body_result]: arm_type=right" in result
        assert "Optimize imports" in result


class TestLotusBodyFallback:
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_no_provider_fallback(self, mock_get_provider):
        mock_get_provider.return_value = None

        result = lotus_body(
            task="Fix typo",
            arm_type="main",
        )

        assert "[task_status]: completed" in result
        assert "Fallback" in result
