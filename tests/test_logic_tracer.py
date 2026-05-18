import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from skills.tool_tianyan.scripts.logic_tracer import trace_error


class TestLogicTracer:
    def test_none_error(self):
        result = trace_error("NoneType has no attribute 'foo'")
        assert "[recommended_skill]: yindan" in result
        assert "[root_cause]: Missing null check" in result

    def test_import_error(self):
        result = trace_error("ImportError: No module named 'missing'")
        assert "[recommended_skill]: yindan" in result
        assert "Import path incorrect" in result

    def test_refactor_request(self):
        result = trace_error("Need to refactor this module")
        assert "[recommended_skill]: sanjian" in result
        assert "RESTRUCTURE" in result or "Structural design" in result

    def test_bulk_cleanup(self):
        result = trace_error("bulk cleanup of deprecated code")
        assert "[recommended_skill]: kaishan" in result

    def test_feature_request(self):
        result = trace_error("implement new payment feature")
        assert "[recommended_skill]: taie" in result

    def test_unknown_error(self):
        result = trace_error("something weird happened")
        assert "[recommended_skill]: yindan" in result
        assert "Insufficient information" in result

    def test_with_log_file(self, tmp_path):
        log = tmp_path / "test.log"
        # Write short log so the tail includes the error line
        log.write_text("Error at line 42\nSome context here", encoding="utf-8")
        result = trace_error("test error", log_file=str(log))
        assert "[log_excerpt]" in result
        assert "Error at line 42" in result
