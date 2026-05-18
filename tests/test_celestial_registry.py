import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from skills.celestial_registry.skill_manifest import parse_skill_manifest


def test_parse_tianyan_manifest():
    manifest = parse_skill_manifest("skills/tool_tianyan/SKILL.md")
    assert manifest["name"] == "tianyan"
    assert "logic_tracer" in [t["name"] for t in manifest["tools"]]
    assert manifest["tools"][0]["parameters"]["error_desc"] == "The description of the error to trace."


def test_parse_missing_file():
    manifest = parse_skill_manifest("skills/tool_nonexistent/SKILL.md")
    assert manifest is None
