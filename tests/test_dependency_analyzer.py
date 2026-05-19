import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from skills.tool_sanjian.scripts.dependency_analyzer import analyze_dependencies


class TestDependencyAnalyzer:
    def test_simple_chain(self, tmp_path):
        a = tmp_path / "a.py"
        b = tmp_path / "b.py"
        a.write_text("import b\n", encoding="utf-8")
        b.write_text("x = 1\n", encoding="utf-8")

        files = [str(a), str(b)]
        result = analyze_dependencies(files, project_root=str(tmp_path))
        assert result["graph"][str(a)] == [str(b)]
        assert result["reverse_deps"][str(b)] == [str(a)]
        assert result["topological_order"] == [str(b), str(a)]
        assert result["circular_deps"] == []

    def test_circular_dependency(self, tmp_path):
        a = tmp_path / "a.py"
        b = tmp_path / "b.py"
        a.write_text("import b\n", encoding="utf-8")
        b.write_text("import a\n", encoding="utf-8")

        files = [str(a), str(b)]
        result = analyze_dependencies(files, project_root=str(tmp_path))
        assert len(result["circular_deps"]) > 0

    def test_interface_boundaries(self, tmp_path):
        base = tmp_path / "base.py"
        a = tmp_path / "a.py"
        b = tmp_path / "b.py"
        c = tmp_path / "c.py"
        base.write_text("x = 1\n", encoding="utf-8")
        a.write_text("import base\n", encoding="utf-8")
        b.write_text("import base\n", encoding="utf-8")
        c.write_text("import base\n", encoding="utf-8")

        files = [str(base), str(a), str(b), str(c)]
        result = analyze_dependencies(files, project_root=str(tmp_path))
        assert str(base) in result["interface_boundaries"]
