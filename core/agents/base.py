"""Agent base class -- defines the contract for all agent components.

An agent is a component with a system prompt, available tools, and the
ability to plan, execute steps, and reflect on results.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, List

from core.shared.base import ComponentMetadata, CoreComponent


class AgentBase(CoreComponent):
    """Base class for agent components.

    Agents have a system prompt that defines their role, a list of available
    tools they can invoke, and a plan-reflect execution loop.

    Subclasses must implement:
        - system_prompt: The agent's role definition.
        - available_tools: Tool definitions the agent can use.
        - plan(): Break a task into execution steps.
        - reflect(): Evaluate a step result and decide whether to adjust.
    """

    def __init__(self, metadata: ComponentMetadata) -> None:
        super().__init__(metadata)
        self._system_prompt: str = ""
        self._tools: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the agent's system prompt defining its role and behavior."""

    @property
    @abstractmethod
    def available_tools(self) -> List[Dict[str, Any]]:
        """Return the list of tool definitions available to this agent."""

    @abstractmethod
    def plan(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan the execution steps for a given task.

        Args:
            task: The task description.
            context: Additional context for planning.

        Returns:
            A list of step dictionaries describing the execution plan.
        """

    @abstractmethod
    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Reflect on a step result and decide whether to adjust the plan.

        Args:
            result: The result dictionary from a completed step.

        Returns:
            A dictionary that may contain ``"needs_adjustment": True`` to
            trigger re-planning, along with any other reflection data.
        """

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's plan-reflect loop.

        The loop:
        1. Extract task and context from *input_data*.
        2. Plan execution steps.
        3. Execute each step, reflecting after each one.
        4. If reflection indicates adjustment is needed, re-plan.
        5. Return all steps and results.

        Args:
            input_data: Must contain ``"task"`` (str) and optionally ``"context"`` (dict).

        Returns:
            Dictionary with ``"steps"`` and ``"results"`` lists.
        """
        task = input_data.get("task", "")
        context = input_data.get("context", {})
        steps = self.plan(task, context)
        results: List[Dict[str, Any]] = []
        for step in steps:
            step_result = self._execute_step(step)
            reflection = self.reflect(step_result)
            if reflection.get("needs_adjustment"):
                steps = self.plan(task, {**context, "reflection": reflection})
            results.append(step_result)
        return {"steps": steps, "results": results}

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step from the plan.

        Subclasses can override this to provide step-specific execution logic.
        The default implementation simply returns the step dictionary unchanged.

        Args:
            step: The step dictionary from the plan.

        Returns:
            The step result dictionary.
        """
        return step
