import os
import tempfile

from skills.tool_wanglingguan.scripts.code_caller_tracer import find_callers, check_null_handling


class TestCodeCallerTracer:
    def test_find_callers_php(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a target class
            target_file = os.path.join(tmpdir, "TargetClass.php")
            with open(target_file, 'w') as f:
                f.write("<?php\nclass TargetClass {\n    public function targetMethod() {}\n}\n")

            # Create a caller
            caller_file = os.path.join(tmpdir, "Caller.php")
            with open(caller_file, 'w') as f:
                f.write("<?php\nclass Caller {\n    public function doSomething() {\n")
                f.write("        $t = new TargetClass();\n")
                f.write("        $t->targetMethod();\n")
                f.write("    }\n}\n")

            callers = find_callers(tmpdir, "TargetClass", "targetMethod")
            assert len(callers) == 1
            assert callers[0]['file'] == caller_file
            assert 'targetMethod' in callers[0]['context']

    def test_find_callers_no_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            callers = find_callers(tmpdir, "NonExistent", "method")
            assert len(callers) == 0

    def test_check_null_handling_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.php")
            with open(test_file, 'w') as f:
                f.write("<?php\n")
                f.write("function getData() {\n")
                f.write("    return null;\n")
                f.write("}\n")
                f.write("function caller() {\n")
                f.write("    $data = getData();\n")
                f.write("    if ($data === null) {\n")
                f.write("        return 'empty';\n")
                f.write("    }\n")
                f.write("}\n")

            result = check_null_handling(tmpdir, test_file, 7)
            assert result['has_null_check'] is True
            assert len(result['checks_found']) > 0

    def test_check_null_handling_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.php")
            with open(test_file, 'w') as f:
                f.write("<?php\n")
                f.write("function getData() {\n")
                f.write("    return null;\n")
                f.write("}\n")
                f.write("function caller() {\n")
                f.write("    $data = getData();\n")
                f.write("    return $data;\n")
                f.write("}\n")

            result = check_null_handling(tmpdir, test_file, 7)
            assert result['has_null_check'] is False


class TestFindCallersASTFallback:
    def test_ast_mode_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "module.py")
            with open(test_file, 'w') as f:
                f.write("def helper():\n    pass\n")
                f.write("def main():\n")
                f.write("    helper()\n")

            result = find_callers(tmpdir, "module", "helper", mode="auto")
            assert len(result) == 1
            assert result[0]['file'] == test_file

    def test_regex_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "Caller.php")
            with open(test_file, 'w') as f:
                f.write("<?php\n")
                f.write("class Caller {\n")
                f.write("    public function doSomething() {\n")
                f.write("        $t = new TargetClass();\n")
                f.write("        $t->targetMethod();\n")
                f.write("    }\n")
                f.write("}\n")

            result = find_callers(tmpdir, "TargetClass", "targetMethod", mode="regex")
            assert len(result) == 1
            assert 'targetMethod' in result[0]['context']

    def test_ast_only_mode_no_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.php")
            with open(test_file, 'w') as f:
                f.write("<?php\n")
                f.write("class Caller {\n")
                f.write("    public function doSomething() {\n")
                f.write("        $t->targetMethod();\n")
                f.write("    }\n")
                f.write("}\n")

            result = find_callers(tmpdir, "Caller", "targetMethod", mode="ast")
            assert len(result) == 0  # AST mode returns empty for non-Python files
