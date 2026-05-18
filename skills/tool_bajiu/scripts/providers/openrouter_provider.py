import json
import os
import urllib.request

from .base import ModelProvider


class OpenRouterProvider(ModelProvider):
    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def native_hosts(self) -> list[str]:
        return ["all"]

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENROUTER_API_KEY"))

    def infer(self, system_prompt: str, user_prompt: str, timeout: float) -> str:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        model = os.environ.get("SANJIE_OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        url = "https://openrouter.ai/api/v1/chat/completions"
        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 500,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/zmc576700954/sanjie",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
