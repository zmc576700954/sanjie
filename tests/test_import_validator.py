import os
import tempfile

from skills.tool_wanglingguan.scripts.import_validator import (
    find_imports,
    verify_dependency_direction,
)


class TestImportValidator:
    def test_find_imports_php(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "Test.php")
            with open(test_file, 'w') as f:
                f.write("<?php\n")
                f.write(r"use App\Models\User;" + "\n")
                f.write(r"use Illuminate\Support\Facades\Cache;" + "\n")
                f.write("class Test {}\n")

            imports = find_imports(tmpdir, test_file)
            assert len(imports) == 2
            assert imports[0]['type'] == 'php_use'
            assert 'User' in imports[0]['import']

    def test_find_imports_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("import os\n")
                f.write("from datetime import datetime\n")
                f.write("x = 1\n")

            imports = find_imports(tmpdir, test_file)
            assert len(imports) == 2
            assert any(imp['type'] == 'python_import' for imp in imports)

    def test_verify_dependency_direction_correct(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # A imports B, so arrow A -> B should be correct
            file_a = os.path.join(tmpdir, "ComponentA.php")
            with open(file_a, 'w') as f:
                f.write("<?php\n")
                f.write(r"use App\ComponentB;" + "\n")
                f.write("class ComponentA {}\n")

            file_b = os.path.join(tmpdir, "ComponentB.php")
            with open(file_b, 'w') as f:
                f.write("<?php\n")
                f.write("class ComponentB {}\n")

            result = verify_dependency_direction(tmpdir, "ComponentA", "ComponentB")
            assert result['arrow_correct'] is True

    def test_verify_dependency_direction_reversed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # B imports A, so arrow A -> B is WRONG, should be B -> A
            file_a = os.path.join(tmpdir, "ComponentA.php")
            with open(file_a, 'w') as f:
                f.write("<?php\n")
                f.write("class ComponentA {}\n")

            file_b = os.path.join(tmpdir, "ComponentB.php")
            with open(file_b, 'w') as f:
                f.write("<?php\n")
                f.write(r"use App\ComponentA;" + "\n")
                f.write("class ComponentB {}\n")

            result = verify_dependency_direction(tmpdir, "ComponentA", "ComponentB")
            assert result['arrow_correct'] is False

    def test_verify_dependency_direction_unknown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = verify_dependency_direction(tmpdir, "NonExistentA", "NonExistentB")
            assert result['arrow_correct'] is None
