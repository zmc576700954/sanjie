"""Tests for core/shared/ utilities -- errors, utils, config, logging."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.shared.errors import (
    AgentsDevelopError,
    ComponentError,
    ComponentNotFoundError,
    ComponentValidationError,
    ConfigError,
    DuplicateComponentError,
    FormatGenerationError,
    FormatValidationError,
    MigrationError,
    TemplateError,
    UnsupportedToolError,
)
from core.shared.utils import (
    ensure_dir,
    load_manifest,
    save_manifest,
    snake_case,
    validate_version,
)
from core.shared.config import Config
from core.shared.logging import get_logger


# ── Error hierarchy tests ────────────────────────────────────────────────────


class TestErrorHierarchy:
    """Tests for the error class hierarchy."""

    def test_base_error(self) -> None:
        err = AgentsDevelopError("test")
        assert str(err) == "test"
        assert isinstance(err, Exception)

    def test_component_errors(self) -> None:
        assert issubclass(ComponentError, AgentsDevelopError)
        assert issubclass(ComponentNotFoundError, ComponentError)
        assert issubclass(DuplicateComponentError, ComponentError)
        assert issubclass(ComponentValidationError, ComponentError)

    def test_migration_errors(self) -> None:
        assert issubclass(MigrationError, AgentsDevelopError)
        assert issubclass(FormatGenerationError, MigrationError)
        assert issubclass(FormatValidationError, MigrationError)
        assert issubclass(UnsupportedToolError, MigrationError)
        assert issubclass(TemplateError, MigrationError)

    def test_config_error(self) -> None:
        assert issubclass(ConfigError, AgentsDevelopError)

    def test_unsupported_tool_error_message(self) -> None:
        err = UnsupportedToolError("my_tool")
        assert "my_tool" in str(err)

    def test_error_catch_by_base(self) -> None:
        """All custom errors can be caught by AgentsDevelopError."""
        errors = [
            ComponentNotFoundError("a"),
            DuplicateComponentError("b"),
            ComponentValidationError("c"),
            FormatGenerationError("d"),
            FormatValidationError("e"),
            UnsupportedToolError("f"),
            TemplateError("g"),
            ConfigError("h"),
        ]
        for err in errors:
            assert isinstance(err, AgentsDevelopError)


# ── Utils tests ──────────────────────────────────────────────────────────────


class TestSnakeCase:
    """Tests for the snake_case utility function."""

    def test_camel_case(self) -> None:
        assert snake_case("MyComponent") == "my_component"

    def test_pascal_case_multi_word(self) -> None:
        assert snake_case("CodeSecurityScanner") == "code_security_scanner"

    def test_kebab_case(self) -> None:
        assert snake_case("some-kebab-name") == "some_kebab_name"

    def test_space_separated(self) -> None:
        assert snake_case("hello world") == "hello_world"

    def test_already_snake(self) -> None:
        assert snake_case("already_snake_case") == "already_snake_case"

    def test_lowercase_single_word(self) -> None:
        assert snake_case("test") == "test"

    def test_acronym(self) -> None:
        # Consecutive uppercase is treated as one word, followed by a new word
        assert snake_case("XMLParser") == "xml_parser"

    def test_mixed(self) -> None:
        assert snake_case("My-Cool Component") == "my_cool_component"


class TestValidateVersion:
    """Tests for the validate_version utility function."""

    def test_valid_versions(self) -> None:
        assert validate_version("1.0.0") is True
        assert validate_version("0.1.0") is True
        assert validate_version("10.20.30") is True

    def test_invalid_versions(self) -> None:
        assert validate_version("1.0") is False
        assert validate_version("v1.0.0") is False
        assert validate_version("1.0.0-alpha") is False
        assert validate_version("") is False
        assert validate_version("abc") is False


class TestManifestIO:
    """Tests for load_manifest and save_manifest."""

    def test_save_and_load(self, temp_dir: Path) -> None:
        data = {
            "name": "test_comp",
            "type": "skill",
            "version": "1.0.0",
            "description": "A test component",
        }
        path = temp_dir / "manifest.json"
        save_manifest(path, data)

        assert path.exists()
        loaded = load_manifest(path)
        assert loaded == data

    def test_save_creates_parent_dirs(self, temp_dir: Path) -> None:
        path = temp_dir / "nested" / "dir" / "manifest.json"
        save_manifest(path, {"key": "value"})
        assert path.exists()

    def test_load_missing_file(self, temp_dir: Path) -> None:
        path = temp_dir / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_manifest(path)

    def test_load_invalid_json(self, temp_dir: Path) -> None:
        path = temp_dir / "bad.json"
        path.write_text("not valid json {{{", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_manifest(path)


class TestEnsureDir:
    """Tests for the ensure_dir utility."""

    def test_creates_dir(self, temp_dir: Path) -> None:
        new_dir = temp_dir / "new" / "nested" / "dir"
        assert not new_dir.exists()
        ensure_dir(new_dir)
        assert new_dir.is_dir()

    def test_existing_dir_no_error(self, temp_dir: Path) -> None:
        ensure_dir(temp_dir)  # Already exists
        assert temp_dir.is_dir()


# ── Config tests ─────────────────────────────────────────────────────────────


class TestConfig:
    """Tests for the Config class."""

    def test_defaults(self) -> None:
        cfg = Config()
        assert cfg.get("project_name") == "agents-develop"
        assert cfg.get("log_level") == "INFO"
        assert cfg.get("nonexistent") is None

    def test_get_with_default(self) -> None:
        cfg = Config()
        assert cfg.get("missing_key", 42) == 42

    def test_set_and_get(self) -> None:
        cfg = Config()
        cfg.set("custom_key", "custom_value")
        assert cfg.get("custom_key") == "custom_value"

    def test_nested_set_and_get(self) -> None:
        cfg = Config()
        cfg.set("server.host", "localhost")
        cfg.set("server.port", 8080)
        assert cfg.get("server.host") == "localhost"
        assert cfg.get("server.port") == 8080

    def test_load_json_file(self, temp_dir: Path) -> None:
        config_path = temp_dir / "config.json"
        config_path.write_text(
            json.dumps({"custom": "from_file", "project_name": "overridden"}),
            encoding="utf-8",
        )
        cfg = Config(path=config_path)
        assert cfg.get("custom") == "from_file"
        assert cfg.get("project_name") == "overridden"

    def test_save_json_file(self, temp_dir: Path) -> None:
        config_path = temp_dir / "output.json"
        cfg = Config(data={"test_key": "test_value"})
        cfg.path = config_path
        cfg.save()

        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        assert loaded["test_key"] == "test_value"

    def test_save_without_path_raises(self) -> None:
        cfg = Config()
        with pytest.raises(ConfigError):
            cfg.save()

    def test_init_with_data(self) -> None:
        cfg = Config(data={"my_key": "my_val"})
        assert cfg.get("my_key") == "my_val"

    def test_data_property(self) -> None:
        cfg = Config(data={"k": "v"})
        assert cfg.data["k"] == "v"


# ── Logging tests ────────────────────────────────────────────────────────────


class TestLogging:
    """Tests for the get_logger utility."""

    def test_returns_logger(self) -> None:
        import logging

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_custom_level(self) -> None:
        import logging

        logger = get_logger("test_level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_same_name_returns_same_logger(self) -> None:
        l1 = get_logger("same_logger")
        l2 = get_logger("same_logger")
        assert l1 is l2
