"""
Functional tests for all skills/*/scripts/ modules.
Verifies that SKILL.md can correctly reference and call scripts.
"""
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_sanjian_task_decomposer():
    from skills.sanjian.scripts.task_decomposer import decompose
    result = decompose("Need to refactor these modules", ["file_a.py", "file_b.py"])
    assert len(result["subtasks"]) == 2
    assert result["subtasks"][0]["operation"] == "RESTRUCTURE"
    assert result["execution_order"] == ["subtask_1", "subtask_2"]
    print("  [PASS] sanjian/task_decomposer")


def test_sanjian_scope_guardian():
    from skills.sanjian.scripts.scope_guardian import check_scope
    # SAFE -> SAFE = PROCEED
    r = check_scope({"id": "s1", "scope_level": "SAFE"}, current_scope="SAFE")
    assert r["action"] == "PROCEED"
    assert r["approved"] is True
    # SAFE -> BOUNDARY (auto) = EXPAND
    r2 = check_scope({"id": "s2", "scope_level": "BOUNDARY"}, current_scope="SAFE", auto_approve=True)
    assert r2["action"] == "EXPAND"
    assert r2["authorized_scope"] == "BOUNDARY"
    print("  [PASS] sanjian/scope_guardian")


def test_sanjian_executor():
    from skills.sanjian.scripts.executor import execute_write
    tmp = os.path.join(tempfile.gettempdir(), "sanjian_exec_test.py")
    # Create original
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("x = 1\n")
    # Write new content
    r = execute_write(tmp, "y = 2\n", operation="REWRITE")
    assert r["success"] is True
    assert r["backup_path"] is not None
    assert os.path.exists(r["backup_path"])
    with open(tmp, "r", encoding="utf-8") as f:
        assert f.read() == "y = 2\n"
    os.remove(tmp)
    os.remove(r["backup_path"])
    print("  [PASS] sanjian/executor (write + backup)")


def test_sanjian_executor_rollback():
    from skills.sanjian.scripts.executor import execute_write
    tmp = os.path.join(tempfile.gettempdir(), "sanjian_rollback_test.py")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("good = True\n")
    r = execute_write(tmp, "def broken(\n", operation="REWRITE")
    assert r["success"] is False
    with open(tmp, "r", encoding="utf-8") as f:
        assert f.read() == "good = True\n"
    os.remove(tmp)
    print("  [PASS] sanjian/executor (rollback on syntax error)")


def test_sanjian_result_integrator():
    from skills.sanjian.scripts.result_integrator import integrate_results
    results = [
        {"success": True, "backup_path": "/tmp/a.bak"},
        {"success": False, "message": "error"},
        {"action": "HALT"},
    ]
    r = integrate_results(results)
    assert r["succeeded"] == 1
    assert r["failed"] == 1
    assert r["skipped"] == 1
    assert r["status"] == "PARTIAL"
    print("  [PASS] sanjian/result_integrator")


def test_sanjian_dependency_analyzer():
    from skills.sanjian.scripts.dependency_analyzer import analyze_dependencies
    # Test with non-existent files (should not crash)
    r = analyze_dependencies(["nonexist_a.py", "nonexist_b.py"], ".")
    assert "graph" in r
    assert "topological_order" in r
    print("  [PASS] sanjian/dependency_analyzer")


def test_yindan_precise_fix():
    from skills.yindan.scripts.precise_fix import precise_replace
    tmp = os.path.join(tempfile.gettempdir(), "yindan_test.py")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("x = 1\ny = 2\n")
    r = precise_replace(tmp, "x = 1", "x = 42")
    assert "Success" in r
    with open(tmp, "r", encoding="utf-8") as f:
        assert "x = 42" in f.read()
    # Test not found
    r2 = precise_replace(tmp, "zzz_not_here", "abc")
    assert "Error" in r2
    os.remove(tmp)
    print("  [PASS] yindan/precise_fix")


def test_taie_standard_write():
    from skills.taie.scripts.standard_write import write_with_validation
    tmp = os.path.join(tempfile.gettempdir(), "taie_test.py")
    r = write_with_validation(tmp, "def hello():\n    return 42\n")
    assert "Success" in r
    # Test regression: empty function body
    r2 = write_with_validation(tmp, "def empty():\n    pass\n")
    assert "Error" in r2
    # Verify rollback
    with open(tmp, "r", encoding="utf-8") as f:
        assert "hello" in f.read()
    os.remove(tmp)
    print("  [PASS] taie/standard_write")


def test_taie_risk_assessor():
    from skills.taie.scripts.risk_assessor import assess_risk
    r = assess_risk("test.py", "add new function", auto_approve=True)
    assert r["approved"] is True
    assert "Risk Assessment" in r["report"]
    print("  [PASS] taie/risk_assessor")


def test_tianyan_logic_tracer():
    from skills.tianyan.scripts.logic_tracer import trace_error
    r = trace_error("TypeError: NoneType has no attribute x")
    assert "[recommended_skill]: yindan" in r
    r2 = trace_error("Need to refactor the entire auth module")
    assert "[recommended_skill]: sanjian" in r2
    r3 = trace_error("bulk cleanup of deprecated files")
    assert "[recommended_skill]: kaishan" in r3
    print("  [PASS] tianyan/logic_tracer")


def test_bajiu_task_analyzer():
    from skills.bajiu_xuangong.scripts.task_analyzer import analyze_task, route_task
    profiles = [
        {"name": "yindan", "description": "precision fix", "tools": ["precise_fix"]},
        {"name": "sanjian", "description": "refactoring", "tools": ["executor"]},
        {"name": "kaishan", "description": "bulk delete", "tools": ["bulk_delete"]},
    ]
    r = analyze_task("fix this single line bug", profiles)
    assert r["difficulty"] == "TRIVIAL"
    assert r["matched_candidates"][0]["name"] == "yindan"

    r2 = analyze_task("refactor the entire module across multiple files", profiles)
    assert r2["difficulty"] == "COMPLEX"
    assert r2["matched_candidates"][0]["name"] == "sanjian"

    # Test routing
    r3 = route_task("some task\n[recommended_skill]: kaishan\n[action]: delete", "CRITICAL", [])
    assert r3["execution_plan"][0]["skill"] == "kaishan"
    print("  [PASS] bajiu_xuangong/task_analyzer")


def test_bajiu_skill_scanner():
    from skills.bajiu_xuangong.scripts.skill_scanner import scan_skills
    # Mock a simple skill library
    class MockSkill:
        def __init__(self, name, desc):
            self.name = name
            self.description = desc
        def get_tools(self):
            return []

    class MockLibrary:
        def get_all_skills(self):
            return [MockSkill("tianyan", "investigate"), MockSkill("yindan", "fix")]

    r = scan_skills(MockLibrary())
    assert r["total_skills"] == 2
    assert len(r["skill_profiles"]) == 2
    print("  [PASS] bajiu_xuangong/skill_scanner")


def test_kaishan_blast_assessor():
    from skills.kaishan.scripts.blast_assessor import assess_blast_radius
    test_dir = os.path.join(tempfile.gettempdir(), "kaishan_test_dir")
    os.makedirs(test_dir, exist_ok=True)
    for i in range(3):
        with open(os.path.join(test_dir, f"test_{i}.tmp"), "w") as f:
            f.write("x")
    r = assess_blast_radius(test_dir, r".*\.tmp", auto_approve=True)
    assert r["approved"] is True
    assert len(r["affected_files"]) == 3
    shutil.rmtree(test_dir)
    print("  [PASS] kaishan/blast_assessor")


def test_kaishan_bulk_operations():
    from skills.kaishan.scripts.bulk_operations import bulk_delete, global_replace
    test_dir = os.path.join(tempfile.gettempdir(), "kaishan_bulk_test")
    os.makedirs(test_dir, exist_ok=True)
    files = []
    for i in range(2):
        p = os.path.join(test_dir, f"del_{i}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("content")
        files.append(p)
    r = bulk_delete(files)
    assert "Deleted 2 files" in r
    assert not os.path.exists(files[0])
    shutil.rmtree(test_dir, ignore_errors=True)
    print("  [PASS] kaishan/bulk_operations")


if __name__ == "__main__":
    print("=" * 50)
    print("Skills Scripts Functional Tests")
    print("=" * 50)
    test_sanjian_task_decomposer()
    test_sanjian_scope_guardian()
    test_sanjian_executor()
    test_sanjian_executor_rollback()
    test_sanjian_result_integrator()
    test_sanjian_dependency_analyzer()
    test_yindan_precise_fix()
    test_taie_standard_write()
    test_taie_risk_assessor()
    test_tianyan_logic_tracer()
    test_bajiu_task_analyzer()
    test_bajiu_skill_scanner()
    test_kaishan_blast_assessor()
    test_kaishan_bulk_operations()
    print("=" * 50)
    print("ALL 14 TESTS PASSED")
    print("=" * 50)
