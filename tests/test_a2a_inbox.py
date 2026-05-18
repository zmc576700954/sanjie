import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_a2a_directory_structure():
    inbox_dir = os.path.join(project_root, "a2a_inbox")
    assert os.path.exists(inbox_dir)
    assert os.path.exists(os.path.join(inbox_dir, "pending"))
    assert os.path.exists(os.path.join(inbox_dir, "claimed"))
    assert os.path.exists(os.path.join(inbox_dir, "completed"))
