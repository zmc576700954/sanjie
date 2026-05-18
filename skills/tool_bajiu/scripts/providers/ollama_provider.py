import json
import os
import socket
import urllib.request

from .base import ModelProvider


class OllamaProvider(ModelProvider):
    @property
    def name(self) -> str:
        return "ollama"

    @property
    def native_hosts(self) -> list[str]:
        return ["all"]

    def is_available(self) -> bool:
        host = os.environ.get("SANJIE_OLLAMA_HOST", "localhost:11434")
        try:
            conn = urllib.request.urlopen(
                f"http://{host}/api/tags",
                timeout=2,
            )
            conn.close()
            return True
        except Exception:
            return False

    def infer(self, system_prompt: str, user_prompt: str, timeout: float) -> str:
        host = os.environ.get("SANJIE_OLLAMA_HOST", "localhost:11434")
        model = os.environ.get("SANJIE_OLLAMA_MODEL", "llama3")
        url = f"http://{host}/api/generate"
        body = json.dumps(
            {
                "model": model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "options": {"temperature": 0.1},
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
        return data["response"]
