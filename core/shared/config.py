"""Configuration management for agents_develop.

Provides a Config class that loads, reads, and writes YAML or JSON config
files with support for default values and nested key access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from core.shared.errors import ConfigError

# Lazy import for yaml -- it may not be installed
_yaml = None


def _get_yaml():
    """Lazily import the yaml module."""
    global _yaml
    if _yaml is None:
        try:
            import yaml

            _yaml = yaml
        except ImportError:
            _yaml = False
    if _yaml is False:
        raise ConfigError("PyYAML is not installed; install it with `pip install pyyaml`")
    return _yaml


_DEFAULT_CONFIG: Dict[str, Any] = {
    "project_name": "agents-develop",
    "default_tools": ["claude", "zcode", "cursor", "reasionix", "mcp"],
    "output_dir": "components",
    "templates_dir": "formats",
    "log_level": "INFO",
}


class Config:
    """Configuration manager that loads and saves YAML or JSON files.

    Attributes:
        path: Path to the config file.
        data: The configuration dictionary.
    """

    def __init__(
        self,
        path: Optional[Path] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize configuration.

        Args:
            path: Path to a config file (YAML or JSON). If provided and the file
                  exists, it will be loaded. If not, defaults are used.
            data: Optional dictionary to seed the config with. Overrides defaults
                  but is itself overridden by values loaded from file.
        """
        self._data: Dict[str, Any] = {**_DEFAULT_CONFIG}
        if data:
            self._data.update(data)

        self.path = path
        if path is not None:
            if path.exists():
                self._load_file(path)
            else:
                # Store defaults but don't write yet -- user calls save() explicitly
                pass

    def _load_file(self, path: Path) -> None:
        """Load configuration from a YAML or JSON file.

        Args:
            path: Path to the config file.

        Raises:
            ConfigError: If the file format is unsupported or the file cannot be read.
        """
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigError(f"Cannot read config file: {exc}") from exc

        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            yaml = _get_yaml()
            file_data = yaml.safe_load(text) or {}
        elif suffix == ".json":
            file_data = json.loads(text)
        else:
            raise ConfigError(f"Unsupported config file format: {suffix}")

        if not isinstance(file_data, dict):
            raise ConfigError("Config file must contain a mapping at the top level")

        self._data.update(file_data)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Supports dot-separated nested keys, e.g. ``"server.port"``.

        Args:
            key: The configuration key (dot-separated for nested access).
            default: Default value if the key is not found.

        Returns:
            The configuration value, or *default* if the key does not exist.
        """
        parts = key.split(".")
        current: Any = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Supports dot-separated nested keys. Intermediate dicts are created
        automatically.

        Args:
            key: The configuration key (dot-separated for nested access).
            value: The value to set.
        """
        parts = key.split(".")
        current = self._data
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to a file.

        Args:
            path: Path to write to. Falls back to self.path if not given.

        Raises:
            ConfigError: If no path is available or the format is unsupported.
        """
        target = path or self.path
        if target is None:
            raise ConfigError("No config file path specified; pass path= to save()")

        target.parent.mkdir(parents=True, exist_ok=True)
        suffix = target.suffix.lower()
        if suffix in (".yaml", ".yml"):
            yaml = _get_yaml()
            text = yaml.dump(self._data, default_flow_style=False, allow_unicode=True)
        elif suffix == ".json":
            text = json.dumps(self._data, indent=2, ensure_ascii=False)
        else:
            raise ConfigError(f"Unsupported config file format: {suffix}")

        target.write_text(text, encoding="utf-8")

    @property
    def data(self) -> Dict[str, Any]:
        """Return the raw configuration dictionary."""
        return self._data
