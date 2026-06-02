"""LLM client abstraction supporting Anthropic and OpenAI providers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    content: str
    stop_reason: str  # "end_turn" | "tool_use" | "stop" | "tool_calls"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-20250514"
OPENAI_DEFAULT_MODEL = "gpt-4o"


class LLMClient:
    """Unified LLM client supporting Anthropic and OpenAI."""

    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        api_key: str | None = None,
    ):
        self.provider = provider

        if provider == "anthropic":
            if anthropic is None:
                raise ImportError("anthropic package not installed: pip install anthropic")
            self._client = anthropic.Anthropic(api_key=api_key)
            self.model = model or ANTHROPIC_DEFAULT_MODEL
        elif provider == "openai":
            if openai is None:
                raise ImportError("openai package not installed: pip install openai")
            self._client = openai.OpenAI(api_key=api_key)
            self.model = model or OPENAI_DEFAULT_MODEL
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'anthropic' or 'openai'.")

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat request and return a unified response."""
        if self.provider == "anthropic":
            return self._chat_anthropic(messages, tools, max_tokens)
        else:
            return self._chat_openai(messages, tools, max_tokens)

    def _chat_anthropic(self, messages, tools, max_tokens) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = self._client.messages.create(**kwargs)

        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return LLMResponse(
            content="\n".join(text_parts),
            stop_reason=response.stop_reason,
            tool_calls=tool_calls,
        )

    def _chat_openai(self, messages, tools, max_tokens) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = [_to_openai_tool(t) for t in tools]
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            import json
            for tc in choice.message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments),
                })

        return LLMResponse(
            content=choice.message.content or "",
            stop_reason=choice.finish_reason,
            tool_calls=tool_calls,
        )


def _to_openai_tool(anthropic_tool: dict) -> dict:
    """Convert Anthropic tool schema to OpenAI function schema."""
    return {
        "type": "function",
        "function": {
            "name": anthropic_tool["name"],
            "description": anthropic_tool.get("description", ""),
            "parameters": anthropic_tool.get("input_schema", {}),
        },
    }
