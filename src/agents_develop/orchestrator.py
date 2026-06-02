"""Orchestrator — routes and chains SubAgents.

Supports sequential pipeline, parallel fan-out, and error-aware degradation
per SubAgent best practices section 1.1.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .llm_client import LLMClient
from .agents.investigator import Investigator
from .agents.reviewer import Reviewer
from .agents.fixer import Fixer
from .agents.documenter import Documenter
from .base import CircuitBreakerOpen, BudgetExhausted
from .skill_bridge import route_to_skill, SkillProfile
from .schemas import (
    AgentHandoff,
    InvestigateInput, InvestigateOutput,
    FixInput, FixOutput,
    ReviewInput, ReviewOutput,
    DocumentInput, DocumentOutput,
    TokenBudget, TracingSpan, PipelineResult,
)

logger = logging.getLogger(__name__)


class Orchestrator:
    """Routes requests and chains SubAgents into pipelines.

    Features:
    - Token budget control across the entire pipeline
    - Parallel fan-out for independent tasks (e.g., multi-file review)
    - Error-aware degradation (partial failures don't block the pipeline)
    - Agent handoff protocol for structured context passing
    - Tracing spans for observability
    """

    def __init__(
        self,
        llm_client: LLMClient,
        token_budget: TokenBudget | None = None,
    ):
        self.llm = llm_client
        self.token_budget = token_budget or TokenBudget(total=200_000)
        self._investigator = Investigator(llm_client, token_budget=self.token_budget)
        self._reviewer = Reviewer(llm_client, token_budget=self.token_budget)
        self.tracing_spans: list[TracingSpan] = []

    def investigate(self, input: InvestigateInput) -> InvestigateOutput:
        """Run investigation only."""
        try:
            return self._investigator.run(input)
        except BudgetExhausted as e:
            logger.error(f"Investigation aborted: {e}")
            raise
        except CircuitBreakerOpen as e:
            logger.error(f"Investigation degraded: {e}")
            raise

    def fix(self, input: FixInput) -> FixOutput:
        """Investigate (if needed) then fix with handoff protocol."""
        if not input.investigation:
            inv_input = InvestigateInput(
                error_description=input.error_description,
                source_files=input.target_files,
            )
            input.investigation = self.investigate(inv_input)

        # Build handoff context from investigation
        handoff = self._build_handoff(input.investigation)
        # Inject handoff as context into fix input
        if not input.error_description and input.investigation:
            input.error_description = (
                f"Root cause: {input.investigation.root_cause}\n"
                f"Action: {input.investigation.recommended_action}\n"
                f"Affected: {', '.join(input.investigation.affected_files)}"
            )

        fixer = Fixer(self.llm, token_budget=self.token_budget)
        return fixer.run(input)

    def review(self, input: ReviewInput) -> ReviewOutput:
        """Run review only."""
        return self._reviewer.run(input)

    def fix_and_review(self, input: FixInput) -> dict:
        """Pipeline: investigate → fix → review.

        Review runs after fix even if fix has issues (error-aware degradation).
        """
        stages = []
        fix_result = None
        fix_error = None

        # Stage 1: Fix
        try:
            fix_result = self.fix(input)
            stages.append({"agent": "Fixer", "status": "success", "output": fix_result.model_dump()})
        except (BudgetExhausted, CircuitBreakerOpen, Exception) as e:
            fix_error = str(e)
            stages.append({"agent": "Fixer", "status": "error", "error": fix_error})
            logger.warning(f"Fix stage failed: {e}")

        # Stage 2: Review (runs even if fix failed — error-aware degradation)
        review_result = None
        try:
            review_target = input.target_files[0] if input.target_files else "."
            review_result = self.review(ReviewInput(
                target_path=review_target,
                review_types=["security", "quality"],
            ))
            stages.append({"agent": "Reviewer", "status": "success", "output": review_result.model_dump()})
        except Exception as e:
            stages.append({"agent": "Reviewer", "status": "error", "error": str(e)})
            logger.warning(f"Review stage failed: {e}")

        return {
            "fix": fix_result,
            "review": review_result,
            "error": fix_error,
            "stages": stages,
        }

    def parallel_review(self, paths: list[str], review_types: list[str] | None = None) -> list[ReviewOutput]:
        """Parallel fan-out: review multiple files concurrently.

        Per best practice section 1.1: independent subtasks run in parallel.
        """
        if review_types is None:
            review_types = ["format", "security", "quality"]

        results: list[ReviewOutput | None] = [None] * len(paths)
        max_workers = min(len(paths), 4)

        def _review_one(idx: int, path: str) -> tuple[int, ReviewOutput | None]:
            try:
                return idx, self.review(ReviewInput(target_path=path, review_types=review_types))
            except Exception as e:
                logger.warning(f"Parallel review failed for {path}: {e}")
                return idx, None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_review_one, i, path)
                for i, path in enumerate(paths)
            ]
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        return [r for r in results if r is not None]

    def full_pipeline(self, input: FixInput) -> PipelineResult:
        """Full pipeline: investigate → fix → review with tracing.

        Returns PipelineResult with all stage results, handoff history,
        and token usage.
        """
        stages = []
        handoffs = []
        success = True
        error_stages = []

        # Stage 1: Investigate
        investigation = None
        try:
            inv_input = InvestigateInput(
                error_description=input.error_description,
                source_files=input.target_files,
            )
            investigation = self.investigate(inv_input)
            handoff = self._build_handoff(investigation)
            handoffs.append(handoff)
            stages.append({
                "agent": "Investigator",
                "status": "success",
                "output": investigation.model_dump(),
            })
        except Exception as e:
            stages.append({"agent": "Investigator", "status": "error", "error": str(e)})
            error_stages.append("Investigator")
            success = False
            logger.error(f"Investigation failed: {e}")

        # Stage 2: Fix (only if investigation succeeded or has pre-existing investigation)
        fix_result = None
        if investigation or input.investigation:
            try:
                fix_input = FixInput(
                    error_description=input.error_description,
                    investigation=investigation or input.investigation,
                    target_files=input.target_files,
                    safety_level=input.safety_level,
                )
                fix_result = self.fix(fix_input)
                stages.append({
                    "agent": "Fixer",
                    "status": "success",
                    "output": fix_result.model_dump(),
                })
            except Exception as e:
                stages.append({"agent": "Fixer", "status": "error", "error": str(e)})
                error_stages.append("Fixer")
                success = False
                logger.error(f"Fix failed: {e}")

        # Stage 3: Review (always runs — error-aware degradation)
        review_result = None
        try:
            review_target = input.target_files[0] if input.target_files else "."
            review_result = self.review(ReviewInput(
                target_path=review_target,
                review_types=["security", "quality"],
            ))
            stages.append({
                "agent": "Reviewer",
                "status": "success",
                "output": review_result.model_dump(),
            })
        except Exception as e:
            stages.append({"agent": "Reviewer", "status": "error", "error": str(e)})
            error_stages.append("Reviewer")
            logger.error(f"Review failed: {e}")

        # Aggregate tracing spans from all agents
        all_spans = (
            self._investigator.tracing_spans
            + self._reviewer.tracing_spans
        )

        return PipelineResult(
            stages=stages,
            total_tokens=self.token_budget.spent,
            success=success and not error_stages,
            error_stages=error_stages,
            handoffs=handoffs,
        )

    def _build_handoff(self, investigation: InvestigateOutput) -> AgentHandoff:
        """Build standardized handoff from investigation output.

        Per best practice section 3.1-3.2: all agent handoffs use
        structured schemas, not free text.
        """
        return AgentHandoff(
            source_agent="Investigator",
            target_capability="problem_solving",
            tags=["debug", investigation.recommended_action],
            investigation_report=investigation,
            recommended_action=investigation.recommended_action,
            urgency="high" if investigation.confidence > 0.8 else "medium",
            context_summary=investigation.root_cause,
        )

    def document(self, input: DocumentInput) -> DocumentOutput:
        """Run documentation pipeline using Documenter (Taibai bridge)."""
        documenter = Documenter(self.llm, token_budget=self.token_budget)
        return documenter.run(input)

    def route_task(self, task_description: str) -> SkillProfile | None:
        """Route a task to the best matching skill using the skill bridge.

        Returns the skill profile if found, None otherwise.
        Useful for L1 routing decisions per SPEC.md section 4.4.
        """
        return route_to_skill(task_description)
