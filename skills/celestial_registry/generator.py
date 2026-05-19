import os

from skills.celestial_registry.skill_manifest import parse_skill_manifest, MANIFEST_TO_PY_TYPE_STR


def _to_camel_name(name: str) -> str:
    """Convert a snake_case name to CamelCase."""
    return "".join(part.capitalize() for part in name.split("_"))


def _find_skill_dir(skill_name: str) -> str:
    """Find the skill directory by manifest name or directory name.

    Args:
        skill_name: The name field from the manifest or the directory name.

    Returns:
        Path to the SKILL.md file.
    """
    # First try direct directory match
    direct_path = os.path.join("skills", skill_name, "SKILL.md")
    if os.path.isfile(direct_path):
        return direct_path

    # Scan skills/ for a manifest whose 'name' matches
    skills_dir = "skills"
    if os.path.isdir(skills_dir):
        for entry in os.listdir(skills_dir):
            candidate = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.isfile(candidate):
                manifest = parse_skill_manifest(candidate)
                if manifest and manifest.get("name") == skill_name:
                    return candidate

    raise FileNotFoundError(f"Skill manifest not found for skill: {skill_name}")


def generate_mcp_server_code(skill_name: str) -> str:
    """Generate an MCP server Python script from a Skill's SKILL.md manifest.

    Args:
        skill_name: The name of the skill (manifest name or directory under skills/)."""
    skill_md_path = _find_skill_dir(skill_name)
    manifest = parse_skill_manifest(skill_md_path)
    if manifest is None:
        raise FileNotFoundError(f"Skill manifest not found: {skill_md_path}")

    tools = manifest.get("tools", [])
    server_title = f"{_to_camel_name(skill_name)} Server"

    tool_functions = []

    for tool in tools:
        tool_name = tool["name"]
        script_path = tool["script"]
        parameters = tool.get("parameters", {})
        tool_desc = tool.get("description", f"Auto-generated tool {tool_name}")

        # Derive module path and function name from script path
        # e.g. "scripts/logic_tracer.py" -> "skills.tool_tianyan.scripts.logic_tracer"
        script_module = script_path.replace("/", ".").replace("\\", ".").rstrip(".py")
        module_import = f"skills.{skill_name}.{script_module}"
        function_name = os.path.splitext(os.path.basename(script_path))[0]

        # Build parameter signature with pydantic.Field descriptions
        param_defs = []
        for param_name, param_def in parameters.items():
            if isinstance(param_def, dict):
                param_desc = param_def.get("description", "")
                ptype = param_def.get("type", "string")
            else:
                param_desc = str(param_def)
                ptype = "string"

            py_type = MANIFEST_TO_PY_TYPE_STR.get(ptype, "str")

            if "optional" in param_desc.lower():
                param_defs.append(
                    f'    {param_name}: {py_type} = Field(default="", description="{param_desc}")'
                )
            else:
                param_defs.append(
                    f'    {param_name}: {py_type} = Field(description="{param_desc}")'
                )

        param_signature = ",\n".join(param_defs)
        if param_signature:
            param_signature = f"\n{param_signature}\n"

        # Build function call arguments
        call_args = ", ".join(parameters.keys())

        # Build the tool function
        func_code = f'''
@mcp.tool()
def {tool_name}({param_signature}) -> str:
    """{tool_desc}"""
    try:
        from {module_import} import {function_name}
        return {function_name}({call_args})
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))
'''
        tool_functions.append(func_code)

    # We don't need static imports because we import inside each function
    # But the spec says to import them, so let's keep it simple.
    # Actually the spec says: "The function body imports and calls the actual script function"
    # So we do dynamic imports inside the function body.

    tools_code = "\n".join(tool_functions)

    code = f'''import os
import sys
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.utils import ensure_safe_path

mcp = FastMCP("{server_title}")
{tools_code}
if __name__ == "__main__":
    mcp.run()
'''
    return code
