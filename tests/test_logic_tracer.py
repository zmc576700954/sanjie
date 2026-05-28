from skills.tool_tianyan.scripts.logic_tracer import trace_error


class TestLogicTracer:
    # --- Basic error type classification ---
    def test_none_error(self):
        result = trace_error("NoneType has no attribute 'foo'")
        assert "[recommended_skill]: yindan" in result
        assert "[root_cause]: Missing null check" in result
        assert "[confidence]: HIGH" in result
        assert "[detected_error_type]: NoneType" in result

    def test_import_error(self):
        result = trace_error("ImportError: No module named 'missing'")
        assert "[recommended_skill]: yindan" in result
        assert "Import path incorrect" in result
        assert "[detected_error_type]: ImportError" in result

    def test_attribute_error(self):
        result = trace_error("AttributeError: 'str' object has no attribute 'items'")
        assert "[recommended_skill]: yindan" in result
        assert "[detected_error_type]: AttributeError" in result
        assert "[error_detail]: Missing attribute: 'items'" in result

    def test_key_error(self):
        result = trace_error("KeyError: 'user_id'")
        assert "[recommended_skill]: yindan" in result
        assert "[detected_error_type]: KeyError" in result
        assert "[error_detail]: Missing key: 'user_id'" in result

    def test_timeout_error(self):
        result = trace_error("TimeoutError: operation timed out")
        assert "[recommended_skill]: yindan" in result
        assert "[detected_error_type]: TimeoutError" in result

    # --- Action-intent routing (P0 fix: weighted scoring) ---
    def test_refactor_request(self):
        result = trace_error("Need to refactor this module")
        assert "[recommended_skill]: sanjian" in result

    def test_bulk_cleanup(self):
        result = trace_error("bulk cleanup of deprecated code")
        assert "[recommended_skill]: kaishan" in result

    def test_feature_request(self):
        result = trace_error("implement new payment feature")
        assert "[recommended_skill]: taie" in result

    def test_action_intent_wins_over_error_type(self):
        """'refactor the NoneType error handling' should route to sanjian, not yindan."""
        result = trace_error("refactor the NoneType error handling")
        assert "[recommended_skill]: sanjian" in result

    def test_cleanup_wins_over_feature(self):
        """'implement cleanup for deprecated modules' should route to kaishan (cleanup intent)."""
        result = trace_error("implement cleanup for deprecated modules")
        assert "[recommended_skill]: kaishan" in result

    # --- Error detail extraction ---
    def test_error_detail_module_name(self):
        result = trace_error("ImportError: No module named 'requests'")
        assert "[error_detail]: Missing module: 'requests'" in result

    def test_error_detail_import_name(self):
        result = trace_error("cannot import name 'Config' from 'app'")
        assert "[error_detail]: Cannot import name: 'Config'" in result

    def test_error_detail_type_mismatch(self):
        result = trace_error("TypeError: expected str, got int")
        assert "[error_detail]: Expected type str, received int" in result

    # --- Fallback / unknown errors ---
    def test_unknown_error(self):
        result = trace_error("something weird happened")
        assert "[recommended_skill]: yindan" in result
        assert "Insufficient information" in result
        assert "[confidence]: LOW" in result

    def test_empty_error(self):
        result = trace_error("")
        assert "[recommended_skill]: yindan" in result
        assert "[confidence]: LOW" in result

    # --- Source code context (P1 fix: context is now used) ---
    def test_with_source_context_none_hint(self):
        result = trace_error(
            "something failed",
            source_code_context="def get_user():\n    return None\n"
        )
        assert "[source_context_hints]" in result
        assert "[recommended_skill]: yindan" in result

    def test_with_source_context_import_hint(self):
        result = trace_error(
            "module not found",
            source_code_context="import pandas\nfrom os import path\n"
        )
        assert "[source_context_hints]" in result

    # --- Log file handling ---
    def test_with_log_file(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("Error at line 42\nSome context here", encoding="utf-8")
        result = trace_error("test error", log_file=str(log))
        assert "[log_excerpt]" in result
        assert "Error at line 42" in result

    def test_empty_log_file(self, tmp_path):
        log = tmp_path / "empty.log"
        log.write_text("", encoding="utf-8")
        result = trace_error("test error", log_file=str(log))
        assert "<log file is empty>" in result

    def test_nonexistent_log_file(self, tmp_path):
        result = trace_error("test error", log_file=str(tmp_path / "nope.log"))
        assert "[log_excerpt]" not in result
        assert "[recommended_skill]" in result
