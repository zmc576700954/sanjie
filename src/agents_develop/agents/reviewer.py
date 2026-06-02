"""Reviewer SubAgent — audits code for security, quality, and format compliance."""
import json
from pathlib import Path
from pydantic import BaseModel

from ..base import SubAgent
from ..schemas import ReviewInput, ReviewOutput, TokenBudget
from ..tools.security_scan import scan_file as _scan_file
from ..tools.code_analysis import analyze_complexity

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "reviewer.md"


def _tool_scan_security(input: dict) -> str:
    file_path = input.get("file_path", "")
    scan_types = input.get("scan_types", ["secrets", "sql_injection", "xss", "misconfiguration"])
    findings = _scan_file(file_path, scan_types)
    return json.dumps(findings, indent=2, default=str)


def _tool_analyze_complexity(input: dict) -> str:
    result = analyze_complexity(input.get("file_path", ""))
    return json.dumps(result, indent=2, default=str)


class Reviewer(SubAgent):
    """Audits code for security vulnerabilities, quality issues, and format compliance."""

    def system_prompt(self) -> str:
        if _PROMPT_PATH.exists():
            return _PROMPT_PATH.read_text(encoding="utf-8")
        return (
            "You are a code review specialist. "
            "Audit code for security, quality, and format compliance. "
            "Output JSON matching ReviewOutput schema."
        )

    def tools(self) -> list[dict]:
        return [
            {
                "name": "scan_security",
                "description": "Run security pattern scans on a file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file to scan"},
                        "scan_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Scan types: secrets, sql_injection, xss, misconfiguration",
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "analyze_complexity",
                "description": "Analyze cyclomatic complexity of a Python file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to Python file"},
                    },
                    "required": ["file_path"],
                },
            },
        ]

    def input_schema(self) -> type[BaseModel]:
        return ReviewInput

    def output_schema(self) -> type[BaseModel]:
        return ReviewOutput

    def __init__(self, llm_client, token_budget: TokenBudget | None = None):
        super().__init__(llm_client, token_budget=token_budget)
        self.tool_executor = {
            "scan_security": _tool_scan_security,
            "analyze_complexity": _tool_analyze_complexity,
        }
