import json
import os
import urllib.request

from .base import ModelProvider


class OpenAIProvider(ModelProvider):
    @property
    def name(self) -> str:
        return "openai"

    @property
    def native_hosts(self) -> list[str]:
        return ["cursor", "codex"]

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def infer(self, system_prompt: str, user_prompt: str, timeout: float) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("SANJIE_OPENAI_MODEL", "gpt-4o-mini")
        url = f"{base_url}/chat/completions"
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
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
