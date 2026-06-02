"""Pydantic models for SubAgent I/O."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class Finding(BaseModel):
    """A single review finding."""
    severity: str          # critical / high / warning / note / TODO
    location: str          # "file.py:line" or description
    description: str
    fix_suggestion: str = ""


class InvestigateInput(BaseModel):
    """Input for the Investigator SubAgent."""
    error_description: str
    source_files: list[str] = []
    log_file: str | None = None


class InvestigateOutput(BaseModel):
    """Output from the Investigator SubAgent."""
    root_cause: str
    logic_chain: list[str]
    affected_files: list[str]
    recommended_action: str        # fix / refactor / guard
    confidence: float              # 0.0 - 1.0


class FixInput(BaseModel):
    """Input for the Fixer SubAgent."""
    error_description: str = ""
    investigation: InvestigateOutput | None = None
    target_files: list[str]
    safety_level: str = "standard"  # strict / standard / aggressive


class FixOutput(BaseModel):
    """Output from the Fixer SubAgent."""
    modified_files: list[str]
    changes_summary: str
    tests_passed: bool


class ReviewInput(BaseModel):
    """Input for the Reviewer SubAgent."""
    target_path: str
    review_types: list[str] = ["format", "security", "quality"]


class ReviewOutput(BaseModel):
    """Output from the Reviewer SubAgent."""
    verdict: str                     # approved / needs_revision
    findings: list[Finding]
    risk_summary: dict[str, int]     # severity -> count


# --- Agent Handoff Protocol (Best Practice 3.1-3.2) ---


class AgentHandoff(BaseModel):
    """Standardized handoff context between SubAgents.

    Per best practices: all SubAgent handoffs use structured schemas,
    not free text. L1 runtime parses [next_action] for routing.
    """
    source_agent: str                                    # who produced this
    target_capability: str                               # capability domain for routing
    tags: list[str] = []                                 # routing tags
    investigation_report: InvestigateOutput | None = None
    recommended_action: str = ""                         # fix / refactor / guard
    urgency: str = "medium"                              # critical / high / medium / low
    boundary_checks: list[dict] = []                     # BC-XXX findings
    security_findings: list[dict] = []                   # SA-XXX findings
    context_summary: str = ""                            # compressed context for target


# --- Token Budget Control (Best Practice 7.2) ---


class TokenBudget(BaseModel):
    """Token budget for cost control across agent pipelines."""
    total: int = 100_000
    spent: int = 0

    def remaining(self) -> int:
        return max(0, self.total - self.spent)

    def check(self, estimated: int) -> bool:
        """Return True if estimated spend fits within budget."""
        return self.spent + estimated <= self.total

    def record(self, tokens_used: int):
        self.spent += tokens_used

    @property
    def is_exhausted(self) -> bool:
        return self.spent >= self.total


# --- Observability (Best Practice 6.1) ---


class TracingSpan(BaseModel):
    """Distributed tracing span for agent/tool execution."""
    span_id: str
    parent_span_id: str | None = None
    agent_name: str
    operation: str                 # e.g. "investigate", "tool:trace_error"
    status: str = "running"       # running / success / error
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = None
    token_usage: int = 0
    error_message: str | None = None


# --- Pipeline Result ---


class PipelineResult(BaseModel):
    """Aggregated result from an orchestrated pipeline."""
    stages: list[dict]           # list of stage results with agent name and output
    total_tokens: int = 0
    success: bool = True
    error_stages: list[str] = [] # stages that failed
    handoffs: list[AgentHandoff] = []


# --- Document Agent I/O (Best Practice - Taibai) ---


class DocumentInput(BaseModel):
    """Input for the Documenter SubAgent."""
    source_paths: list[str]
    doc_type: str = "spec"       # spec / archive / handoff / memory
    author: str = "agents-develop"


class DocumentOutput(BaseModel):
    """Output from the Documenter SubAgent."""
    output_path: str
    doc_type: str
    sections: list[str] = []
    claims_marked: dict[str, int] = {}  # verified/inferred/unverified counts
    compressed: bool = False
