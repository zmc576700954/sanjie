"""Host environment probe for detecting available LLM capabilities."""

import os
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError


API_KEY_VARS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "OPENROUTER_API_KEY",
]


def _detect_host() -> str:
    """Detect the IDE/host environment using heuristics."""
    if os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_CODE_1"):
        return "claude_code"

    if os.environ.get("CURSOR_MCP"):
        return "cursor"

    if os.environ.get("GEMINI_CLI"):
        return "gemini_cli"

    if os.environ.get("CODEX") or os.environ.get("OPENAI_CODEX"):
        return "codex"

    if os.environ.get("TRAE"):
        return "trae"

    # Check for project-level markers
    if Path(".claude").exists():
        return "claude_code"

    # Check for home-directory markers
    home = Path.home()
    if (home / ".cursor").exists():
        return "cursor"
    if (home / ".trae").exists():
        return "trae"

    return "none"


def _has_api_key() -> bool:
    """Check whether any known API key environment variable is set."""
    return any(os.environ.get(var) for var in API_KEY_VARS)


def _has_ollama() -> bool:
    """Check whether Ollama is running on localhost:11434."""
    try:
        with urlopen("http://localhost:11434/api/tags", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def _available_providers() -> list:
    """Return a list of available provider names."""
    providers = []

    if os.environ.get("OPENAI_API_KEY"):
        providers.append("openai")
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers.append("anthropic")
    if os.environ.get("GOOGLE_API_KEY"):
        providers.append("google")
    if os.environ.get("OPENROUTER_API_KEY"):
        providers.append("openrouter")
    if _has_ollama():
        providers.append("ollama")

    return providers


def detect_host_environment() -> dict:
    """Detect the host environment and available LLM capabilities.

    Returns:
        dict with keys:
            - host: detected IDE host
            - has_ollama: whether localhost:11434 is reachable
            - has_api_key: whether any known API key env var is set
            - available_providers: list of provider names available
    """
    return {
        "host": _detect_host(),
        "has_ollama": _has_ollama(),
        "has_api_key": _has_api_key(),
        "available_providers": _available_providers(),
    }
