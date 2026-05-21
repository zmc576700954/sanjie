from unittest.mock import MagicMock, patch

from skills.tool_nezha.scripts.demon_hunt import demon_hunt
from skills.tool_nezha.scripts.lotus_body import lotus_body
from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode
from skills.tool_nezha.scripts.assignment_planner import create_assignment_plan


class TestNezhaIntegration:
    """End-to-end integration tests for the Nezha toolkit."""

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

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_single_head_investigation(self, mock_get_provider):
        """Simple task: single cognitive head investigation."""
        mock_provider = MagicMock()
        mock_provider.infer.return_value = (
            '{"root_causes": [{"id": "RC-001", "description": "Missing null check", "evidence": "line 42"}], '
            '"business_risks": [], "code_risks": [], '
            '"suggested_fixes": [{"id": "SF-001", "priority": "P0", "files_affected": ["core.py"], "description": "Add null check"}]}'
        )
        mock_get_provider.return_value = mock_provider

        report = demon_hunt(
            target="core.py",
            mode="bug_hunt",
            head_type="cognitive",
        )

        assert "[task_status]: completed" in report
        assert "[demon_hunt_result]: head_type=cognitive" in report
        assert "[root_cause]" in report
        assert "Missing null check" in report
        assert "[next_action]" in report
        assert "[persona_handoff]" in report
        mock_provider.infer.assert_called_once()

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    def test_l1_orchestrated_three_heads(self, mock_get_provider):
        """L1 orchestrates three separate demon_hunt calls (no Python orchestrator)."""
        mock_provider = MagicMock()
        mock_provider.infer.side_effect = [
            # business head
            '{"findings": [{"id": "B001", "severity": "high", "description": "Business violation", "scenario": "edge"}]}',
            # code head
            '{"findings": [{"id": "C001", "severity": "critical", "category": "null_pointer", "description": "Null risk", "pattern": "missing"}]}',
            # cognitive head
            '{"root_causes": [{"id": "RC001", "confidence": "high", "description": "Root found", "evidence": "line 42", "surface_symptom": "crash", "true_nature": "missing validation"}], "suggested_fixes": [{"id": "SF001", "priority": "P0", "description": "Fix validation", "files_affected": ["core.py"]}]}',
        ]
        mock_get_provider.return_value = mock_provider

        # L1 calls each head separately (simulating parallel orchestration)
        business_report = demon_hunt(target="core.py", mode="bug_hunt", head_type="business")
        code_report = demon_hunt(target="core.py", mode="bug_hunt", head_type="code")
        cognitive_report = demon_hunt(target="core.py", mode="bug_hunt", head_type="cognitive")

        assert "head_type=business" in business_report
        assert "head_type=code" in code_report
        assert "head_type=cognitive" in cognitive_report
        assert "Business violation" in business_report
        assert "Null risk" in code_report
        assert "Root found" in cognitive_report
        assert mock_provider.infer.call_count == 3

    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_l1_orchestrated_three_arms(self, mock_get_provider):
        """L1 orchestrates three separate lotus_body calls (no Python orchestrator)."""
        mock_provider = MagicMock()
        mock_provider.infer.side_effect = [
            '{"execution_plan": [{"id": "EP-M1"}], "execution_result": [{"id": "EP-M1", "status": "success", "diff_summary": "Fixed core", "files_modified": ["core.py"]}]}',
            '{"execution_plan": [{"id": "EP-L1"}], "execution_result": [{"id": "EP-L1", "status": "success", "diff_summary": "Added boundary", "files_modified": ["handlers.py"]}]}',
            '{"execution_plan": [{"id": "EP-R1"}], "execution_result": [{"id": "EP-R1", "status": "success", "diff_summary": "Optimized", "files_modified": ["utils.py"]}]}',
        ]
        mock_get_provider.return_value = mock_provider

        main_result = lotus_body(task="Fix core", arm_type="main")
        left_result = lotus_body(task="Add boundaries", arm_type="left")
        right_result = lotus_body(task="Optimize structure", arm_type="right")

        assert "arm_type=main" in main_result
        assert "arm_type=left" in left_result
        assert "arm_type=right" in right_result
        assert mock_provider.infer.call_count == 3

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

        assert set(all_assigned) == set(files)
        assert len(all_assigned) == len(set(all_assigned))

    @patch("skills.tool_nezha.scripts.demon_hunt.get_available_provider")
    @patch("skills.tool_nezha.scripts.lotus_body.get_available_provider")
    def test_output_schema_compliance(self, mock_lotus_provider, mock_demon_provider):
        """Verify all outputs follow [block_name]: value format per SPEC.md."""
        mock_demon = MagicMock()
        mock_demon.infer.return_value = (
            '{"root_causes": [{"id": "RC001", "description": "Root found"}], '
            '"business_risks": [], "code_risks": [], "suggested_fixes": []}'
        )
        mock_demon_provider.return_value = mock_demon

        report = demon_hunt(target="test.py", head_type="cognitive")

        # Required blocks per SPEC.md
        assert "[task_status]:" in report
        assert "[output_summary]:" in report
        assert "[capability_used]:" in report
        assert "[tags]:" in report
        assert "[next_action]:" in report
        assert "[persona_handoff]:" in report

        mock_lotus = MagicMock()
        mock_lotus.infer.return_value = (
            '{"execution_plan": [{"id": "EP-001"}], '
            '"execution_result": [{"id": "EP-001", "status": "success", "diff_summary": "Done"}], '
            '"verification_checklist": []}'
        )
        mock_lotus_provider.return_value = mock_lotus

        result = lotus_body(task="Fix it", arm_type="main")

        assert "[task_status]:" in result
        assert "[output_summary]:" in result
        assert "[capability_used]:" in result
        assert "[tags]:" in result
        assert "[next_action]:" in result
        assert "[persona_handoff]:" in result
