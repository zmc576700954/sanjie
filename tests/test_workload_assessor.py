from skills.tool_nezha.scripts.workload_assessor import assess_workload, ExecutionMode


class TestWorkloadAssessor:
    def test_single_head_simple(self):
        result = assess_workload(
            file_count=1,
            line_change_est=30,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.SINGLE_HEAD

    def test_single_head_boundary(self):
        result = assess_workload(
            file_count=2,
            line_change_est=50,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.SINGLE_HEAD

    def test_dual_head_moderate(self):
        result = assess_workload(
            file_count=3,
            line_change_est=100,
            complexity="moderate",
            risk_level="medium",
        )
        assert result == ExecutionMode.DUAL_HEAD

    def test_trinity_high_file_count(self):
        result = assess_workload(
            file_count=6,
            line_change_est=100,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS

    def test_trinity_high_lines(self):
        result = assess_workload(
            file_count=2,
            line_change_est=250,
            complexity="simple",
            risk_level="low",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS

    def test_trinity_complex(self):
        result = assess_workload(
            file_count=2,
            line_change_est=50,
            complexity="complex",
            risk_level="low",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS

    def test_trinity_critical_risk(self):
        result = assess_workload(
            file_count=1,
            line_change_est=30,
            complexity="simple",
            risk_level="critical",
        )
        assert result == ExecutionMode.TRINITY_SIX_ARMS
