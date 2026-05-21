from skills.tool_nezha.scripts.assignment_planner import (
    create_assignment_plan,
    HeadRole,
    ArmAssignment,
)


class TestAssignmentPlanner:
    def test_single_head_plan(self):
        plan = create_assignment_plan(
            mode="single_head",
            target_files=["core.py"],
            task_description="Fix null pointer",
        )
        assert plan["mode"] == "single_head"
        assert "head_assignments" not in plan or plan.get("head_assignments") is None
        assert "arm_assignments" not in plan or plan.get("arm_assignments") is None

    def test_dual_head_plan(self):
        plan = create_assignment_plan(
            mode="dual_head",
            target_files=["core.py", "utils.py"],
            task_description="Refactor payment logic",
            auxiliary_head="code_head",
        )
        assert plan["mode"] == "dual_head"
        assert len(plan["head_assignments"]) == 2
        assert "cognitive_head" in plan["head_assignments"]
        assert "code_head" in plan["head_assignments"]

    def test_trinity_head_assignments(self):
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=["core/service.py", "core/model.py", "handlers/edge.py"],
            task_description="Major refactoring",
        )
        assert plan["mode"] == "trinity_six_arms"
        heads = plan["head_assignments"]
        assert len(heads) == 3
        assert "cognitive_head" in heads
        assert "business_head" in heads
        assert "code_head" in heads
        assert heads["cognitive_head"]["role"] == HeadRole.CONTEXT_MASTER.value
        assert heads["business_head"]["role"] == HeadRole.BUSINESS_ANALYZER.value
        assert heads["code_head"]["role"] == HeadRole.CODE_ANALYZER.value

    def test_trinity_arm_assignments(self):
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=["core/service.py", "handlers/edge.py", "utils/helpers.py"],
            task_description="Major refactoring",
        )
        arms = plan["arm_assignments"]
        assert len(arms) == 3
        assert "main_arms" in arms
        assert "left_arms" in arms
        assert "right_arms" in arms
        assert arms["main_arms"]["head"] == "cognitive_head"
        assert arms["left_arms"]["head"] == "business_head"
        assert arms["right_arms"]["head"] == "code_head"
        # Verify execution order
        assert plan["execution_order"][0]["arms"] == ["main_arms"]
        assert plan["execution_order"][1]["arms"] == ["left_arms", "right_arms"]

    def test_arm_scope_no_overlap(self):
        plan = create_assignment_plan(
            mode="trinity_six_arms",
            target_files=["a.py", "b.py", "c.py"],
            task_description="Test",
        )
        arms = plan["arm_assignments"]
        all_files = []
        for arm_name, arm_data in arms.items():
            all_files.extend(arm_data["files"])
        # Each file assigned to exactly one arm
        assert len(all_files) == len(set(all_files))
        assert set(all_files) == {"a.py", "b.py", "c.py"}
