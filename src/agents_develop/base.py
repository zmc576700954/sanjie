"""SubAgent base class with 3-layer error handling, token budget, and tracing."""
from __future__ import annotations

import re
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from .llm_client import LLMClient, LLMResponse
from .schemas import TokenBudget, TracingSpan

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker has tripped after repeated failures."""


class BudgetExhausted(Exception):
    """Raised when the token budget is exhausted."""


class RetryPolicy:
    """Layer 2: Exponential backoff retry for transient LLM failures."""

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        return min(self.base_delay * (2 ** attempt), self.max_delay)


class CircuitBreaker:
    """Layer 3: Circuit breaker to degrade gracefully after repeated failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "closed"  # closed (normal) / open (tripped) / half_open (testing)

    def record_success(self):
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker tripped after {self.failure_count} failures")

    def check(self):
        if self.state == "closed":
            return
        if self.state == "open":
            if self.last_failure_time and time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker is open. Retry after {self.recovery_timeout}s."
                )


class SubAgent(ABC):
    """Base class for all SubAgents with 3-layer error handling.

    Layer 1: Tool-level — tool errors are fed back to LLM for self-correction.
    Layer 2: Node-level — LLM call failures retry with exponential backoff.
    Layer 3: Global — circuit breaker trips after repeated failures, triggering degradation.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        token_budget: TokenBudget | None = None,
    ):
        self.llm = llm_client
        self.tool_executor: dict[str, Callable] = {}
        self.token_budget = token_budget or TokenBudget(total=100_000)
        self.retry_policy = RetryPolicy(max_attempts=3)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5)
        self.tracing_spans: list[TracingSpan] = []

    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    def tools(self) -> list[dict]: ...

    @abstractmethod
    def input_schema(self) -> type[BaseModel]: ...

    @abstractmethod
    def output_schema(self) -> type[BaseModel]: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def run(self, input_data: BaseModel) -> BaseModel:
        """Execute the SubAgent: LLM + tool loop until final answer."""
        # Layer 3: Check circuit breaker before starting
        self.circuit_breaker.check()

        span = TracingSpan(
            span_id=f"{self.name}-{id(input_data)}",
            agent_name=self.name,
            operation="run",
        )
        self.tracing_spans.append(span)

        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": input_data.model_dump_json()},
        ]

        max_iterations = 10
        consecutive_errors = 0

        try:
            for iteration in range(max_iterations):
                # Check token budget before each LLM call
                if self.token_budget.is_exhausted:
                    raise BudgetExhausted(
                        f"Token budget exhausted ({self.token_budget.spent}/{self.token_budget.total})"
                    )

                # Layer 2: LLM call with retry
                response = self._call_llm_with_retry(messages)

                if response.stop_reason in ("tool_use", "tool_calls") and response.tool_calls:
                    messages.append(self._assistant_message(response))
                    for tc in response.tool_calls:
                        # Layer 1: Tool errors are fed back to LLM as context
                        result = self._execute_tool(tc)
                        messages.append(self._tool_result_message(tc["id"], result))
                    consecutive_errors = 0
                else:
                    output = self._parse_output(response.content)
                    # Success — record in circuit breaker and tracing
                    self.circuit_breaker.record_success()
                    span.status = "success"
                    span.end_time = __import__("datetime").datetime.now()
                    return output

            raise RuntimeError(f"SubAgent exceeded max iterations ({max_iterations})")

        except (CircuitBreakerOpen, BudgetExhausted):
            raise
        except Exception as e:
            self.circuit_breaker.record_failure()
            span.status = "error"
            span.error_message = str(e)
            span.end_time = __import__("datetime").datetime.now()
            raise

    def _call_llm_with_retry(self, messages: list[dict]) -> LLMResponse:
        """Layer 2: Call LLM with exponential backoff retry."""
        last_error = None
        for attempt in range(self.retry_policy.max_attempts):
            try:
                response = self.llm.chat(messages, tools=self.tools())
                self._estimate_and_record_tokens(response)
                return response
            except Exception as e:
                last_error = e
                if attempt < self.retry_policy.max_attempts - 1:
                    delay = self.retry_policy.get_delay(attempt)
                    logger.warning(
                        f"[{self.name}] LLM call failed (attempt {attempt + 1}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)
        raise last_error

    def _estimate_and_record_tokens(self, response: LLMResponse):
        """Estimate token usage from response and record against budget."""
        # Rough estimation: 1 token per 4 chars of content
        estimated = len(response.content) // 4 + 100  # 100 base overhead
        for tc in response.tool_calls:
            estimated += len(str(tc.get("input", ""))) // 4
        self.token_budget.record(estimated)

    def _execute_tool(self, tool_call: dict) -> str:
        """Layer 1: Execute tool and return result.

        Tool errors are returned as feedback strings for LLM self-correction
        rather than raising exceptions.
        """
        name = tool_call["name"]
        inp = tool_call["input"]

        tool_span = TracingSpan(
            span_id=f"{self.name}-tool-{name}-{id(tool_call)}",
            parent_span_id=f"{self.name}-{id(tool_call)}",
            agent_name=self.name,
            operation=f"tool:{name}",
        )
        self.tracing_spans.append(tool_span)

        if name in self.tool_executor:
            try:
                result = self.tool_executor[name](inp)
                tool_span.status = "success"
                tool_span.end_time = __import__("datetime").datetime.now()
                return str(result)
            except Exception as e:
                # Layer 1: Feed error back to LLM for self-correction
                tool_span.status = "error"
                tool_span.error_message = str(e)
                tool_span.end_time = __import__("datetime").datetime.now()
                logger.warning(f"[{self.name}] Tool '{name}' error: {e}")
                return f"Tool error: {e}"
        else:
            tool_span.status = "error"
            tool_span.error_message = f"Tool '{name}' not found"
            tool_span.end_time = __import__("datetime").datetime.now()
            return f"Tool '{name}' not found in executor registry."

    def _parse_output(self, content: str) -> BaseModel:
        """Parse LLM output into the output schema."""
        schema = self.output_schema()
        try:
            return schema.model_validate_json(content)
        except ValidationError:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                return schema.model_validate_json(match.group(1).strip())
            raise

    def _assistant_message(self, response: LLMResponse) -> dict:
        """Build an assistant message for the Anthropic format."""
        blocks = []
        if response.content:
            blocks.append({"type": "text", "text": response.content})
        for tc in response.tool_calls:
            blocks.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["input"],
            })
        return {"role": "assistant", "content": blocks}

    def _tool_result_message(self, tool_use_id: str, result: str) -> dict:
        """Build a tool result message."""
        return {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": result}],
        }
