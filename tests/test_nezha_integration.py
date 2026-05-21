from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.demon_hunt import demon_hunt
from skills.tool_nezha.scripts.lotus_body import lotus_body
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode
from skills.tool_nezha.scripts.assignment_planner import create_assignment_plan


class TestNezhaIntegration:
    """End-to-end integration tests for the full Nezha pipeline."""

    def test_workload_assessment_to_assignment_plan(self):
        """Workload assessment correctly drives assignment plan creation."""
        mode = assess_workload(
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="high",
        )
        assert mode == ExecutionMode.TRINITY_SIX_ARMS

        plan = create_assignment_plan(
            mode=mode.value,
            target_files=["core/a.py", "core/b.py", "handlers/c.py", "utils/d.py"],
            task_description="Major refactoring",
        )
        assert plan["mode"] == "trinity_six_arms"
        assert len(plan["head_assignments"]) == 3
        assert len(plan["arm_assignments"]) == 3

    def test_single_head_pipeline(self):
        """Simple task: single head investigation -> single arms execution."""
        with patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider") as mock_provider:
            mock_ai = MagicMock()
            mock_ai.infer.return_value = (
                '{"root_causes": [{"id": "RC-001", "description": "Missing null check", "evidence": "line 42"}], '
                '"business_risks": [], "code_risks": [], '
                '"suggested_fixes": [{"id": "SF-001", "priority": "P0", "files_affected": ["core.py"], "description": "Add null check"}]}'
            )
            mock_provider.return_value = mock_ai

            report = demon_hunt(
                target="core.py",
                mode="bug_hunt",
                file_count=1,
                line_change_est=10,
                complexity="simple",
                risk_level="low",
            )

        assert "single_head" in report
        assert "[root_cause]" in report
        assert "Missing null check" in report

        # Feed report into lotus_body
        parsed_report = {
            "suggested_fixes": [{"id": "SF-001", "priority": "P0", "files_affected": ["core.py"], "description": "Add null check"}]
        }

        with patch("skills.tool_nezha.scripts.lotus_body.get_available_provider") as mock_provider:
            mock_ai = MagicMock()
            mock_ai.infer.return_value = (
                '{"execution_plan": [{"id": "EP-001", "priority": "P0", "target_file": "core.py", "change_type": "fix", "description": "Add null check"}], '
                '"execution_result": [{"id": "EP-001", "status": "success", "diff_summary": "Added null check", "files_modified": ["core.py"]}], '
                '"verification_checklist": ["[ ] Run tests"]}'
            )
            mock_provider.return_value = mock_ai

            result = lotus_body(
                input_source="demon_hunt_report",
                input_payload=parsed_report,
                file_count=1,
                line_change_est=10,
                complexity="simple",
                risk_level="low",
            )

        assert "single_head" in result
        assert "[execution_result]" in result

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_full_trinity_pipeline(self, mock_lotus_provider, mock_demon_provider):
        """Complex task: trinity investigation -> six arms execution."""
        # Demon hunt: 3 AI calls (business, code, cognitive)
        mock_demon = MagicMock()
        mock_demon.infer.side_effect = [
            '{"findings": [{"id": "B001", "severity": "high", "description": "Business violation", "scenario": "edge"}]}',
            '{"findings": [{"id": "C001", "severity": "critical", "category": "null_pointer", "description": "Null risk", "pattern": "missing"}]}',
            '{"root_causes": [{"id": "RC001", "confidence": "high", "description": "Root found", "evidence": "line 42", "surface_symptom": "crash", "true_nature": "missing validation"}], "suggested_fixes": [{"id": "SF001", "priority": "P0", "description": "Fix validation", "files_affected": ["core.py"]}]}',
        ]
        mock_demon_provider.return_value = mock_demon

        report = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="high",
        )

        assert "trinity_six_arms" in report
        assert "Business violation" in report
        assert "Null risk" in report
        assert mock_demon.infer.call_count == 3

        # Lotus body: 3 AI calls (main, left, right)
        mock_lotus = MagicMock()
        mock_lotus.infer.side_effect = [
            '{"execution_plan": [{"id": "EP-M1", "status": "success"}], "execution_result": [{"id": "EP-M1", "status": "success", "diff_summary": "Fixed core", "files_modified": ["core.py"]}]}',
            '{"execution_plan": [{"id": "EP-L1", "status": "success"}], "execution_result": [{"id": "EP-L1", "status": "success", "diff_summary": "Added boundary", "files_modified": ["handlers.py"]}]}',
            '{"execution_plan": [{"id": "EP-R1", "status": "success"}], "execution_result": [{"id": "EP-R1", "status": "success", "diff_summary": "Optimized", "files_modified": ["utils.py"]}]}',
        ]
        mock_lotus_provider.return_value = mock_lotus

        parsed_report = {
            "suggested_fixes": [{"id": "SF001", "priority": "P0", "files_affected": ["core.py", "handlers.py", "utils.py"], "description": "Fix validation"}]
        }
        result = lotus_body(
            input_source="demon_hunt_report",
            input_payload=parsed_report,
            file_count=8,
            line_change_est=400,
            complexity="complex",
            risk_level="high",
        )

        assert "trinity_six_arms" in result
        assert "main_arms" in result
        assert "left_arms" in result
        assert "right_arms" in result
        assert mock_lotus.infer.call_count == 3

    def test_no_overlap_in_trinity_assignment(self):
        """Verify trinity assignment distributes files without overlap."""
        files = [f"file_{i}.py" for i in range(10)]
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=files,
            task_description="Test",
        )

        arms = plan["arm_assignments"]
        all_assigned = []
        for arm_name, arm_data in arms.items():
            all_assigned.extend(arm_data["files"])

        # All files assigned
        assert set(all_assigned) == set(files)
        # No duplicates
        assert len(all_assigned) == len(set(all_assigned))
