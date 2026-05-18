import importlib
import inspect
import os
import sys

from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.celestial_registry.loader import discover_skills, load_skill_tools
from skills.utils import ensure_safe_path

mcp = FastMCP("SanJie Auto-Discovery Server")


def _has_manual_server(skill_name: str) -> bool:
    """Check if a manual MCP server exists for the skill."""
    manual_path = os.path.join(
        os.path.dirname(__file__), f"{skill_name}_server.py"
    )
    return os.path.isfile(manual_path)


def _looks_like_path(param_name: str) -> bool:
    """Check if a parameter name suggests it is a file path."""
    lowered = param_name.lower()
    return any(keyword in lowered for keyword in ("path", "file", "dir"))


def _resolve_script_function(skill_name: str, tool: dict):
    """Dynamically import the script module and find the target function."""
    script_path = tool.get("script", "")
    if not script_path:
        return None

    # script_path is like "scripts/logic_tracer.py"
    # Convert to module path: skills.tool_tianyan.scripts.logic_tracer
    module_name = f"skills.{skill_name}.{script_path.replace('/', '.').replace('.py', '')}"

    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None

    # Try to find the primary function in the module.
    # Prefer a function whose name matches the tool name or the script basename.
    candidates = [tool["name"], os.path.basename(script_path).replace(".py", "")]

    for cand in candidates:
        if hasattr(module, cand) and callable(getattr(module, cand)):
            return getattr(module, cand)

    # Fallback: return the first callable that is not a dunder or imported
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if obj.__module__ == module.__name__:
            return obj

    return None


def _build_tool_wrapper(skill_name: str, tool: dict, func):
    """Build a wrapper function with proper signature and guards for FastMCP."""
    tool_name = tool["name"]
    parameters = tool.get("parameters", {})

    # Build the parameter list for the function signature
    param_names = list(parameters.keys())

    def wrapper(**kwargs):
        # Apply ensure_safe_path to any parameter that looks like a path
        for key, value in kwargs.items():
            if _looks_like_path(key) and isinstance(value, str):
                kwargs[key] = ensure_safe_path(value)

        try:
            return func(**kwargs)
        except McpError:
            raise
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

    # Attach metadata for FastMCP
    wrapper.__name__ = tool_name
    wrapper.__doc__ = tool.get("description") or f"Auto-registered tool {tool_name} from {skill_name}"

    # Build pydantic Field annotations for the signature
    sig_params = []
    for pname in param_names:
        pdesc = parameters[pname]
        sig_params.append(
            inspect.Parameter(
                pname,
                inspect.Parameter.KEYWORD_ONLY,
                default=Field(description=pdesc),
                annotation=str,
            )
        )

    wrapper.__signature__ = inspect.Signature(parameters=sig_params, return_annotation=str)

    return wrapper


def _register_skill_tools(skill_name: str):
    """Register all tools for a given skill with the FastMCP instance."""
    tools = load_skill_tools(skill_name)
    for tool in tools:
        func = _resolve_script_function(skill_name, tool)
        if func is None:
            continue

        wrapper = _build_tool_wrapper(skill_name, tool, func)
        mcp.tool()(wrapper)


def main():
    skills = discover_skills()
    for skill_name in skills:
        if _has_manual_server(skill_name):
            continue
        _register_skill_tools(skill_name)


main()

if __name__ == "__main__":
    mcp.run()
