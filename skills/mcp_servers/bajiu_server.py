import os
import sys
from typing import List, Dict, Any
from pydantic import Field
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from skills.tool_bajiu.scripts.task_analyzer import analyze_task, route_task

mcp = FastMCP("Bajiu Routing Server")

@mcp.tool()
def bajiu_analyze_task(
    task_context: str = Field(description="The natural language task to analyze."),
    skill_profiles: List[Dict[str, Any]] = Field(description="List of available skill profile dicts.")
) -> dict:
    """Analyze task context against skill profiles."""
    try:
        return analyze_task(task_context, skill_profiles)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def bajiu_route_task(
    task_context: str = Field(description="The task context."),
    difficulty: str = Field(description="Evaluated difficulty level (e.g., HIGH, LOW)."),
    matched_candidates: List[Dict[str, Any]] = Field(description="List of skills that potentially match.")
) -> dict:
    """Route a task to the correct candidate based on difficulty."""
    try:
        return route_task(task_context, difficulty, matched_candidates)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

if __name__ == "__main__":
    mcp.run()
