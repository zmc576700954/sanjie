"""Fixer SubAgent — applies code fixes based on investigation results."""
from pathlib import Path
from pydantic import BaseModel

from ..base import SubAgent
from ..schemas import FixInput, FixOutput, TokenBudget
from ..tools.code_modification import (
    demon_hunt,
    lotus_body,
    create_assignment_plan,
    assess_workload,
)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "fixer.md"


def _tool_demon_hunt(input: dict) -> str:
    return demon_hunt(
        target=input.get("target", ""),
        mode=input.get("mode", "bug_hunt"),
        head_type=input.get("head_type", "cognitive"),
        context=input.get("context", ""),
    )


def _tool_lotus_body(input: dict) -> str:
    return lotus_body(
        task=input.get("task", ""),
        arm_type=input.get("arm_type", "main"),
        scope_limit=input.get("scope_limit"),
        safety_level=input.get("safety_level", "standard"),
    )


def _tool_create_assignment_plan(input: dict) -> str:
    import json
    result = create_assignment_plan(
        mode=input.get("mode", "single_head"),
        target_files=input.get("target_files", []),
        task_description=input.get("task_description", ""),
        auxiliary_head=input.get("auxiliary_head"),
    )
    return json.dumps(result, indent=2, default=str)


def _tool_assess_workload(input: dict) -> str:
    return assess_workload(
        file_count=input.get("file_count", 1),
        line_change_est=input.get("line_change_est", 50),
        complexity=input.get("complexity", "simple"),
        risk_level=input.get("risk_level", "low"),
    )


class Fixer(SubAgent):
    """Applies code fixes based on investigation reports.

    Integrates Nezha's demon_hunt for targeted investigation and
    lotus_body for code modification. Uses assess_workload to
    determine single-head vs multi-arm execution mode.
    """

    def system_prompt(self) -> str:
        if _PROMPT_PATH.exists():
            return _PROMPT_PATH.read_text(encoding="utf-8")
        return (
            "You are a code fixing specialist. "
            "Apply minimal, surgical fixes based on investigation reports. "
            "Use demon_hunt to investigate from multiple perspectives before fixing. "
            "Use lotus_body to execute code modifications. "
            "Use assess_workload to determine execution mode for complex tasks. "
            "Use create_assignment_plan before multi-arm execution. "
            "Output JSON matching FixOutput schema."
        )

    def tools(self) -> list[dict]:
        return [
            {
                "name": "demon_hunt",
                "description": (
                    "Investigate a target from a specific perspective (business/code/cognitive). "
                    "Use for understanding the problem before applying fixes."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Target file path, code snippet, or problem description.",
                        },
                        "mode": {
                            "type": "string",
                            "description": "bug_hunt | code_review | suspicious_scan",
                        },
                        "head_type": {
                            "type": "string",
                            "description": "business | code | cognitive perspective to analyze from.",
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context (investigation reports, requirements).",
                        },
                    },
                    "required": ["target"],
                },
            },
            {
                "name": "lotus_body",
                "description": (
                    "Execute code modifications from a specific arm perspective. "
                    "Main arms handle core logic, left arms handle boundary conditions, "
                    "right arms handle structure optimization."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The modification task description.",
                        },
                        "arm_type": {
                            "type": "string",
                            "description": "main | left | right arm perspective.",
                        },
                        "scope_limit": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Allowed file modification scope.",
                        },
                        "safety_level": {
                            "type": "string",
                            "description": "strict | standard | aggressive.",
                        },
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "assess_workload",
                "description": (
                    "Assess task workload to determine execution mode. "
                    "Returns single_head, dual_head, or trinity_six_arms."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_count": {
                            "type": "integer",
                            "description": "Number of files involved.",
                        },
                        "line_change_est": {
                            "type": "integer",
                            "description": "Estimated lines of change.",
                        },
                        "complexity": {
                            "type": "string",
                            "description": "simple | moderate | complex.",
                        },
                        "risk_level": {
                            "type": "string",
                            "description": "low | medium | high | critical.",
                        },
                    },
                    "required": ["file_count", "line_change_est", "complexity", "risk_level"],
                },
            },
            {
                "name": "create_assignment_plan",
                "description": (
                    "Create a pre-execution assignment plan for multi-arm execution. "
                    "Must be called before lotus_body for complex tasks."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "description": "single_head | dual_head | trinity_six_arms.",
                        },
                        "target_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of files involved.",
                        },
                        "task_description": {
                            "type": "string",
                            "description": "Description of the task.",
                        },
                        "auxiliary_head": {
                            "type": "string",
                            "description": "For dual_head mode: business_head or code_head.",
                        },
                    },
                    "required": ["mode", "target_files", "task_description"],
                },
            },
        ]

    def input_schema(self) -> type[BaseModel]:
        return FixInput

    def output_schema(self) -> type[BaseModel]:
        return FixOutput

    def __init__(self, llm_client, token_budget: TokenBudget | None = None):
        super().__init__(llm_client, token_budget=token_budget)
        self.tool_executor = {
            "demon_hunt": _tool_demon_hunt,
            "lotus_body": _tool_lotus_body,
            "assess_workload": _tool_assess_workload,
            "create_assignment_plan": _tool_create_assignment_plan,
        }
