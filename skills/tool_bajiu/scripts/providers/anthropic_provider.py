import json
import os
import urllib.request

from .base import ModelProvider


class AnthropicProvider(ModelProvider):
    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def native_hosts(self) -> list[str]:
        return ["claude_code", "trae"]

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def infer(self, system_prompt: str, user_prompt: str, timeout: float) -> str:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        model = os.environ.get("SANJIE_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        url = "https://api.anthropic.com/v1/messages"
        body = json.dumps(
            {
                "model": model,
                "max_tokens": 500,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]
