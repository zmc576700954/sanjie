import os
import socket
from typing import Optional

from .base import ModelProvider

# Import all providers for auto-discovery
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider


# Registry of all providers
_ALL_PROVIDERS: list[type[ModelProvider]] = [
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    OpenRouterProvider,
]

# Mapping of host names to their native provider classes
_HOST_NATIVE_MAP: dict[str, type[ModelProvider]] = {
    "cursor": OpenAIProvider,
    "codex": OpenAIProvider,
    "claude_code": AnthropicProvider,
    "trae": AnthropicProvider,
    "gemini_cli": GeminiProvider,
}


def _get_host() -> str:
    """Detect the current host environment."""
    # Check for known environment indicators
    if os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        return "claude_code"
    if os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        # Check for Cursor-specific env vars if any; fallback to cursor
        return "cursor"
    if os.environ.get("GOOGLE_API_KEY"):
        return "gemini_cli"
    # Default to none if we cannot determine
    return "none"


def get_available_provider(force: Optional[str] = None) -> Optional[ModelProvider]:
    """Return first available provider. Priority: forced > host-native > any available."""
    if force:
        for cls in _ALL_PROVIDERS:
            if cls().name == force:
                provider = cls()
                if provider.is_available():
                    return provider
        return None

    # Try host-native provider first
    host = _get_host()
    native_cls = _HOST_NATIVE_MAP.get(host)
    if native_cls is not None:
        provider = native_cls()
        if provider.is_available():
            return provider

    # Fall back to any available provider in registry order
    for cls in _ALL_PROVIDERS:
        provider = cls()
        if provider.is_available():
            return provider

    return None


def list_providers() -> list[dict]:
    """List all providers with availability status."""
    result = []
    for cls in _ALL_PROVIDERS:
        provider = cls()
        result.append({
            "name": provider.name,
            "available": provider.is_available(),
            "native_hosts": provider.native_hosts,
        })
    return result
