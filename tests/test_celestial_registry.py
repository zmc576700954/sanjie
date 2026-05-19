from skills.celestial_registry.skill_manifest import parse_skill_manifest
from skills.celestial_registry.generator import generate_mcp_server_code
from skills.celestial_registry.loader import discover_skills, load_skill_tools
from skills.celestial_registry.plugin_writer import generate_plugin_json


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


def test_discover_skills():
    skills_list = discover_skills()
    assert "tianyan" in skills_list
    assert "taibai" in skills_list


def test_load_skill_tools():
    tools = load_skill_tools("tianyan")
    assert len(tools) >= 1
    assert tools[0]["name"] == "logic_tracer"



def test_generate_plugin_json():
    plugin = generate_plugin_json()
    assert plugin["name"] == "sanjie"
    assert any(s["name"] == "taibai-server" for s in plugin.get("mcpServers", []))
    assert plugin.get("autoDiscover") == True
