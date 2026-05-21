import json
import os
import subprocess
import sys
import tempfile

from skills.tool_wanglingguan.scripts.semantic_analyzer import (
    analyze_call_graph,
    extract_dependencies,
    detect_complexity,
    trace_data_flow,
    find_dead_code,
)


class TestAnalyzeCallGraph:
    def test_find_direct_call(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = os.path.join(tmpdir, "caller.py")
            with open(target_file, 'w') as f:
                f.write("def target_func():\n    pass\n")
                f.write("def caller():\n")
                f.write("    target_func()\n")

            result = analyze_call_graph(tmpdir, "target_func")
            assert result['call_sites_found'] == 1
            assert result['call_sites'][0]['call_type'] == 'direct'
            assert result['call_sites'][0]['in_function'] == 'caller'

    def test_find_method_call(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = os.path.join(tmpdir, "caller.py")
            with open(target_file, 'w') as f:
                f.write("class MyClass:\n")
                f.write("    def target_method(self):\n")
                f.write("        pass\n")
                f.write("class Caller:\n")
                f.write("    def do_it(self):\n")
                f.write("        obj = MyClass()\n")
                f.write("        obj.target_method()\n")

            result = analyze_call_graph(tmpdir, "target_method", include_indirect=True)
            assert result['call_sites_found'] == 1
            assert result['call_sites'][0]['call_type'] == 'method_call_via_obj'

    def test_no_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = analyze_call_graph(tmpdir, "nonexistent")
            assert result['call_sites_found'] == 0

    def test_indirect_call_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = os.path.join(tmpdir, "caller.py")
            with open(target_file, 'w') as f:
                f.write("def target():\n    pass\n")
                f.write("def caller():\n")
                f.write("    obj.something.target()\n")

            result = analyze_call_graph(tmpdir, "target", include_indirect=False)
            assert result['call_sites_found'] == 0

    def test_indirect_call_included(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = os.path.join(tmpdir, "caller.py")
            with open(target_file, 'w') as f:
                f.write("def target():\n    pass\n")
                f.write("def caller():\n")
                f.write("    obj.something.target()\n")

            result = analyze_call_graph(tmpdir, "target", include_indirect=True)
            assert result['call_sites_found'] == 1
            assert result['call_sites'][0]['call_type'] == 'indirect_method_call'


class TestExtractDependencies:
    def test_import_regular(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("import os\n")
                f.write("import sys\n")

            result = extract_dependencies(test_file)
            assert len(result) == 2
            assert result[0]['type'] == 'import'
            assert result[0]['module'] == 'os'

    def test_import_from(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("from datetime import datetime\n")
                f.write("from collections import OrderedDict\n")

            result = extract_dependencies(test_file)
            assert len(result) == 2
            assert result[0]['type'] == 'from_import'
            assert result[0]['module'] == 'datetime'

    def test_import_alias(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("import numpy as np\n")

            result = extract_dependencies(test_file)
            assert len(result) == 1
            assert result[0]['alias'] == 'np'

    def test_import_star(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("from module import *\n")

            result = extract_dependencies(test_file)
            assert len(result) == 1
            assert result[0]['is_star'] is True

    def test_file_not_found(self):
        result = extract_dependencies("/nonexistent/path.py")
        assert 'error' in result[0]


class TestDetectComplexity:
    def test_simple_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def simple():\n")
                f.write("    return 1\n")

            result = detect_complexity(test_file)
            assert result['max_complexity'] == 1
            assert len(result['functions']) == 1
            assert result['functions'][0]['complexity'] == 1

    def test_function_with_if(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def with_if(x):\n")
                f.write("    if x:\n")
                f.write("        return 1\n")
                f.write("    return 0\n")

            result = detect_complexity(test_file)
            assert result['functions'][0]['complexity'] == 2
            assert result['max_complexity'] == 2

    def test_function_with_for_and_if(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def complex_func(items):\n")
                f.write("    for item in items:\n")
                f.write("        if item:\n")
                f.write("            return item\n")
                f.write("    return None\n")

            result = detect_complexity(test_file)
            assert result['functions'][0]['complexity'] == 3  # base + for + if

    def test_nested_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def outer():\n")
                f.write("    def inner():\n")
                f.write("        pass\n")
                f.write("    inner()\n")

            result = detect_complexity(test_file)
            assert len(result['functions']) == 2
            names = {f['name'] for f in result['functions']}
            assert 'outer' in names
            assert 'inner' in names

    def test_file_not_found(self):
        result = detect_complexity("/nonexistent/path.py")
        assert 'error' in result


class TestTraceDataFlow:
    def test_simple_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def process(data):\n")
                f.write("    user_input = request.form['name']\n")
                f.write("    result = eval(user_input)\n")
                f.write("    return result\n")

            result = trace_data_flow(tmpdir, "request", "eval")
            assert len(result) >= 1
            assert result[0]['variable'] == 'user_input'
            assert result[0]['sink_type'] == 'call:eval'

    def test_propagated_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def process():\n")
                f.write("    raw = input('prompt')\n")
                f.write("    processed = raw.strip()\n")
                f.write("    exec(processed)\n")

            result = trace_data_flow(tmpdir, "input", "exec")
            assert len(result) >= 1
            # Variable 'processed' is propagated from 'raw'
            flow = [r for r in result if r['variable'] == 'processed']
            assert len(flow) >= 1
            assert flow[0]['is_propagated'] is True

    def test_no_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def safe():\n")
                f.write("    x = 1 + 2\n")
                f.write("    return x\n")

            result = trace_data_flow(tmpdir, "request", "eval")
            assert len(result) == 0


class TestFindDeadCode:
    def test_unused_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = os.path.join(tmpdir, "main.py")
            with open(main_file, 'w') as f:
                f.write("def used():\n")
                f.write("    return 1\n")
                f.write("def unused():\n")
                f.write("    return 2\n")
                f.write("used()\n")

            result = find_dead_code(tmpdir, ["main.py"])
            assert len(result) == 1
            assert result[0]['name'] == 'unused'

    def test_all_used(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = os.path.join(tmpdir, "main.py")
            with open(main_file, 'w') as f:
                f.write("def func1():\n")
                f.write("    return 1\n")
                f.write("def func2():\n")
                f.write("    return 2\n")
                f.write("func1()\n")
                f.write("func2()\n")

            result = find_dead_code(tmpdir, ["main.py"])
            assert len(result) == 0

    def test_skip_dunder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = os.path.join(tmpdir, "main.py")
            with open(main_file, 'w') as f:
                f.write("def __init__(self):\n")
                f.write("    pass\n")
                f.write("def main():\n")
                f.write("    pass\n")

            result = find_dead_code(tmpdir, ["main.py"])
            assert len(result) == 0


class TestTreeSitterCallGraph:
    """Multi-language call graph analysis via tree-sitter."""

    def test_php_call_graph(self):
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

            result = analyze_call_graph(tmpdir, "targetMethod")
            assert result['call_sites_found'] >= 1
            assert any('targetMethod' in site['context'] for site in result['call_sites'])

    def test_javascript_call_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "app.js")
            with open(test_file, 'w') as f:
                f.write("function targetFunc() { return 1; }\n")
                f.write("function main() {\n")
                f.write("    targetFunc();\n")
                f.write("}\n")

            result = analyze_call_graph(tmpdir, "targetFunc")
            assert result['call_sites_found'] >= 1
            assert any('targetFunc' in site['context'] for site in result['call_sites'])

    def test_typescript_call_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "app.ts")
            with open(test_file, 'w') as f:
                f.write("function targetFunc(): number { return 1; }\n")
                f.write("function main(): void {\n")
                f.write("    targetFunc();\n")
                f.write("}\n")

            result = analyze_call_graph(tmpdir, "targetFunc")
            assert result['call_sites_found'] >= 1
            assert any('targetFunc' in site['context'] for site in result['call_sites'])

    def test_go_call_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "main.go")
            with open(test_file, 'w') as f:
                f.write("package main\n")
                f.write("func targetFunc() int { return 1 }\n")
                f.write("func main() {\n")
                f.write("    targetFunc()\n")
                f.write("}\n")

            result = analyze_call_graph(tmpdir, "targetFunc")
            assert result['call_sites_found'] >= 1
            assert any('targetFunc' in site['context'] for site in result['call_sites'])


class TestTreeSitterDependencies:
    """Multi-language dependency extraction via tree-sitter."""

    def test_php_dependencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "Test.php")
            with open(test_file, 'w') as f:
                f.write("<?php\n")
                f.write("use App\\Models\\User;\n")
                f.write("use Illuminate\\Support\\Facades\\Cache;\n")
                f.write("class Test {}\n")

            result = extract_dependencies(test_file)
            assert len(result) == 2
            assert all(r['type'] == 'php_use' for r in result)

    def test_javascript_dependencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "app.js")
            with open(test_file, 'w') as f:
                f.write("import { useState } from 'react';\n")
                f.write("import axios from 'axios';\n")

            result = extract_dependencies(test_file)
            assert len(result) >= 1
            assert all(r['type'] == 'js_import' for r in result)

    def test_go_dependencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "main.go")
            with open(test_file, 'w') as f:
                f.write("package main\n")
                f.write('import "fmt"\n')
                f.write('import "net/http"\n')

            result = extract_dependencies(test_file)
            assert len(result) == 2
            assert all(r['type'] == 'go_import' for r in result)
            assert any('fmt' in r.get('package', '') for r in result)


class TestSemanticAnalyzerCLI:
    """Test CLI entry points via subprocess."""

    def _run_cli(self, *args):
        cmd = [sys.executable, "-m", "skills.tool_wanglingguan.scripts.semantic_analyzer", *args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def test_cli_call_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "module.py")
            with open(test_file, 'w') as f:
                f.write("def target():\n    pass\n")
                f.write("def main():\n")
                f.write("    target()\n")

            result = self._run_cli("call_graph", "--project", tmpdir, "--method", "target")
            assert result.returncode == 0, f"stderr: {result.stderr}"
            data = json.loads(result.stdout)
            assert data["call_sites_found"] == 1
            assert data["call_sites"][0]["call_type"] == "direct"

    def test_cli_dependencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("import os\n")
                f.write("import sys\n")

            result = self._run_cli("dependencies", "--file", test_file)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert len(data) == 2
            assert data[0]["module"] == "os"

    def test_cli_complexity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def simple():\n")
                f.write("    return 1\n")

            result = self._run_cli("complexity", "--file", test_file)
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["max_complexity"] == 1
            assert data["total_functions"] == 1

    def test_cli_data_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def process():\n")
                f.write("    name = request.form['name']\n")
                f.write("    eval(name)\n")

            result = self._run_cli("data_flow", "--project", tmpdir, "--source", "request", "--sink", "eval")
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert len(data) >= 1
            assert data[0]["variable"] == "name"

    def test_cli_dead_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main_file = os.path.join(tmpdir, "main.py")
            with open(main_file, 'w') as f:
                f.write("def used():\n")
                f.write("    return 1\n")
                f.write("def unused():\n")
                f.write("    return 2\n")
                f.write("used()\n")

            result = self._run_cli("dead_code", "--project", tmpdir, "--entry-points", "main.py")
            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert len(data) == 1
            assert data[0]["name"] == "unused"
