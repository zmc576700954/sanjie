"""Investigator SubAgent — diagnoses errors and traces root causes."""
import json
from pathlib import Path
from pydantic import BaseModel

from ..base import SubAgent
from ..schemas import InvestigateInput, InvestigateOutput, TokenBudget
from ..tools.code_analysis import trace_error, cross_verify, analyze_complexity

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "investigator.md"


def _tool_trace_error(input: dict) -> str:
    return trace_error(
        error_desc=input.get("error_desc", ""),
        source_code_context=input.get("source_code_context", ""),
    )


def _tool_cross_verify(input: dict) -> str:
    return cross_verify(
        local_logic=input.get("local_logic", ""),
        official_spec=input.get("official_spec", ""),
    )


def _tool_analyze_complexity(input: dict) -> str:
    result = analyze_complexity(input.get("file_path", ""))
    return json.dumps(result, indent=2)


class Investigator(SubAgent):
    """Diagnoses errors, traces logic chains, identifies root causes."""

    def system_prompt(self) -> str:
        if _PROMPT_PATH.exists():
            return _PROMPT_PATH.read_text(encoding="utf-8")
        return (
            "You are a code investigation specialist. "
            "Diagnose errors, trace logic chains, identify root causes with evidence. "
            "Output JSON matching InvestigateOutput schema."
        )

    def tools(self) -> list[dict]:
        return [
            {
                "name": "trace_error",
                "description": "Trace an error through code context to find root cause.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "error_desc": {"type": "string", "description": "Error description or message"},
                        "source_code_context": {"type": "string", "description": "Optional source code snippet"},
                    },
                    "required": ["error_desc"],
                },
            },
            {
                "name": "cross_verify",
                "description": "Cross-verify local implementation logic against official specification.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "local_logic": {"type": "string", "description": "Local code logic summary"},
                        "official_spec": {"type": "string", "description": "Official specification text"},
                    },
                    "required": ["local_logic", "official_spec"],
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
        return InvestigateInput

    def output_schema(self) -> type[BaseModel]:
        return InvestigateOutput

    def __init__(self, llm_client, token_budget: TokenBudget | None = None):
        super().__init__(llm_client, token_budget=token_budget)
        self.tool_executor = {
            "trace_error": _tool_trace_error,
            "cross_verify": _tool_cross_verify,
            "analyze_complexity": _tool_analyze_complexity,
        }
