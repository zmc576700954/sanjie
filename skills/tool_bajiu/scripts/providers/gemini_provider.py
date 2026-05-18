import json
import os
import urllib.request

from .base import ModelProvider


class GeminiProvider(ModelProvider):
    @property
    def name(self) -> str:
        return "gemini"

    @property
    def native_hosts(self) -> list[str]:
        return ["gemini_cli"]

    def is_available(self) -> bool:
        return bool(os.environ.get("GOOGLE_API_KEY"))

    def infer(self, system_prompt: str, user_prompt: str, timeout: float) -> str:
        api_key = os.environ.get("GOOGLE_API_KEY")
        model = os.environ.get("SANJIE_GEMINI_MODEL", "gemini-2.0-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        combined = f"{system_prompt}\n\n{user_prompt}"
        body = json.dumps(
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": combined}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 500,
                },
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]
