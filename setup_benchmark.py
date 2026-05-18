import os

# Create the directory structure
os.makedirs("tests/benchmarks/level2_linkage/app/", exist_ok=True)

# Create models.py
with open("tests/benchmarks/level2_linkage/app/models.py", "w") as f:
    f.write("class User:\n    def __init__(self, name):\n        self.name = name\n")

# Create services.py
with open("tests/benchmarks/level2_linkage/app/services.py", "w") as f:
    f.write("from .models import User\n\ndef get_user(name):\n    return User(name)\n")

# Create controller.py
with open("tests/benchmarks/level2_linkage/app/controller.py", "w") as f:
    f.write("from .services import get_user\n\ndef run():\n    return get_user('test')\n")

# Create requirements.txt
with open("tests/benchmarks/level2_linkage/requirements.txt", "w") as f:
    f.write("pytest\n")

# Create verify_bug.py
with open("tests/benchmarks/level2_linkage/verify_bug.py", "w") as f:
    f.write("import sys\nimport os\n\n# Add the app directory to sys.path if needed, but it's a module package\n# The goal is to trigger the Import Error as described in the benchmark scenario\ntry:\n    from app.controller import run\n    print(run())\nexcept ImportError as e:\n    print(f'Caught expected error: {e}')\n    sys.exit(0)\nexcept Exception as e:\n    print(f'Unexpected error: {e}')\n    sys.exit(1)\n")
