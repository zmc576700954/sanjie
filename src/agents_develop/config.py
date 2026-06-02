"""Configuration management for agents-develop."""
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_DIR = Path.home() / ".agents-develop"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    provider: str = "anthropic"
    model: str | None = None
    api_key: str | None = None

    def __post_init__(self):
        if self.api_key is None:
            if self.provider == "anthropic":
                self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif self.provider == "openai":
                self.api_key = os.environ.get("OPENAI_API_KEY")

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return cls(**data)
        return cls()

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def set_value(self, key: str, value: str):
        if key == "provider":
            self.provider = value
        elif key == "model":
            self.model = value
        elif key == "key":
            self.api_key = value
        else:
            raise ValueError(f"Unknown config key: {key}")
        self.save()
