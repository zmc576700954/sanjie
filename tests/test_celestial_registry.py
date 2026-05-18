import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from skills.celestial_registry.skill_manifest import parse_skill_manifest
from skills.celestial_registry.generator import generate_mcp_server_code


def test_parse_tianyan_manifest():
    manifest = parse_skill_manifest("skills/tool_tianyan/SKILL.md")
    assert manifest["name"] == "tianyan"
    assert "logic_tracer" in [t["name"] for t in manifest["tools"]]
    assert manifest["tools"][0]["parameters"]["error_desc"] == "The description of the error to trace."


def test_parse_missing_file():
    manifest = parse_skill_manifest("skills/tool_nonexistent/SKILL.md")
    assert manifest is None


def test_generate_mcp_server_for_tianyan():
    code = generate_mcp_server_code("tianyan")
    assert "def logic_tracer(" in code
    assert "from skills.utils import ensure_safe_path" in code
    assert "mcp = FastMCP" in code
    assert "@mcp.tool()" in code
    assert 'if __name__ == "__main__":' in code
