"""Tests for agents-dev docs CLI."""

from click.testing import CliRunner

from cli.main import main


def test_docs_init_creates_structure():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        result = runner.invoke(main, ["docs", "init", "--path", fs])
        assert result.exit_code == 0
        assert "Initialized" in result.output
