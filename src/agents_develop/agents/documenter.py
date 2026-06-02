"""Documenter SubAgent — bridges to Taibai skill for documentation tasks.

Wraps the Taibai documentation skill (GSSC pipeline, context compression)
as a SubAgent with proper I/O schemas, enabling orchestrated documentation
workflows alongside investigation, fixing, and review.
"""
from pathlib import Path
from pydantic import BaseModel

from ..base import SubAgent
from ..schemas import DocumentInput, DocumentOutput, TokenBudget
from ..tools.doc_tools import compress_context, run_gssc_pipeline

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "documenter.md"


def _tool_gssc_pipeline(input: dict) -> str:
    import json
    result = run_gssc_pipeline(
        source_paths=input.get("source_paths", []),
        doc_type=input.get("doc_type", "spec"),
        aggressive_compress=input.get("aggressive_compress", False),
        output_path=input.get("output_path"),
    )
    return json.dumps(result, indent=2, default=str)


def _tool_compress_context(input: dict) -> str:
    return compress_context(
        file_path=input.get("file_path", ""),
        aggressive=input.get("aggressive", False),
    )


class Documenter(SubAgent):
    """Documentation specialist bridging to the Taibai skill.

    Wraps the GSSC pipeline (Gather→Select→Structure→Compress) and
    context compression tools from the Taibai skill as SubAgent tools.
    """

    def system_prompt(self) -> str:
        if _PROMPT_PATH.exists():
            return _PROMPT_PATH.read_text(encoding="utf-8")
        return (
            "You are a documentation specialist. "
            "Use gssc_pipeline to produce structured technical documentation. "
            "Use compress_context to reduce verbose logs or conversation history. "
            "Output JSON matching DocumentOutput schema."
        )

    def tools(self) -> list[dict]:
        return [
            {
                "name": "gssc_pipeline",
                "description": (
                    "Run the GSSC pipeline: Gather→Select→Structure→Compress. "
                    "Produces structured technical documentation from source files."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file or directory paths to process.",
                        },
                        "doc_type": {
                            "type": "string",
                            "description": "Document type: spec | archive | handoff | memory.",
                        },
                        "aggressive_compress": {
                            "type": "boolean",
                            "description": "Enable aggressive compression.",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional path to write output.",
                        },
                    },
                    "required": ["source_paths"],
                },
            },
            {
                "name": "compress_context",
                "description": (
                    "Compress verbose text or conversation logs to reduce token load. "
                    "Useful for context window management."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file containing verbose text.",
                        },
                        "aggressive": {
                            "type": "boolean",
                            "description": "Enable aggressive compression (strips comments).",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        ]

    def input_schema(self) -> type[BaseModel]:
        return DocumentInput

    def output_schema(self) -> type[BaseModel]:
        return DocumentOutput

    def __init__(self, llm_client, token_budget: TokenBudget | None = None):
        super().__init__(llm_client, token_budget=token_budget)
        self.tool_executor = {
            "gssc_pipeline": _tool_gssc_pipeline,
            "compress_context": _tool_compress_context,
        }
