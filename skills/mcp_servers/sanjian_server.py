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
from skills.tool_sanjian.scripts.dependency_analyzer import analyze_dependencies
from skills.tool_sanjian.scripts.executor import execute_write
from skills.tool_sanjian.scripts.result_integrator import integrate_results
from skills.tool_sanjian.scripts.scope_guardian import check_scope
from skills.tool_sanjian.scripts.task_decomposer import decompose
from skills.mcp_servers.utils import ensure_safe_path

mcp = FastMCP("Sanjian Refactoring Server")

@mcp.tool()
def sanjian_analyze_dependencies(
    target_files: List[str] = Field(description="List of absolute or relative file paths to analyze dependencies for."),
    project_root_dir: str = Field(default="", description="Optional project root directory. Defaults to workspace root.")
) -> dict:
    """Analyze code dependencies for target files."""
    try:
        safe_files = [ensure_safe_path(f) for f in target_files]
        return analyze_dependencies(safe_files, project_root_dir)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def sanjian_execute_write(
    filepath: str = Field(description="The path to the file to write/modify."),
    content: str = Field(description="The new content to write to the file."),
    operation: str = Field(default="REWRITE", description="Operation type (e.g., REWRITE)."),
    backup: bool = Field(default=True, description="Whether to create a backup before modifying.")
) -> dict:
    """Execute a file write operation for refactoring."""
    mcp.info(f"Refactoring file: {filepath}")
    try:
        safe_path = ensure_safe_path(filepath)
        return execute_write(safe_path, content, operation, backup)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def sanjian_integrate_results(
    execution_results: List[Dict[str, Any]] = Field(description="List of execution result dicts from subtasks."),
    task_context: str = Field(default="", description="The overall task context string.")
) -> dict:
    """Integrate results from multiple subtasks."""
    try:
        return integrate_results(execution_results, task_context)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def sanjian_check_scope(
    subtask: Dict[str, Any] = Field(description="Subtask dictionary to check."),
    current_scope: str = Field(default="SAFE", description="Current authorization scope."),
    auto_approve: bool = Field(default=False, description="Whether to auto-approve the execution.")
) -> dict:
    """Check scope of subtask execution."""
    try:
        return check_scope(subtask, current_scope, auto_approve)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

@mcp.tool()
def sanjian_decompose(
    task_context: str = Field(description="The natural language task description/context."),
    target_files: List[str] = Field(description="List of files intended to be modified.")
) -> dict:
    """Decompose a complex refactoring task into subtasks."""
    try:
        safe_files = [ensure_safe_path(f) for f in target_files]
        return decompose(task_context, safe_files)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

if __name__ == "__main__":
    mcp.run()
