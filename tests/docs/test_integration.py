"""Integration tests for DocHub end-to-end workflows."""

from pathlib import Path

from click.testing import CliRunner

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool
from cli.main import main


def test_full_cli_workflow():
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        init_result = runner.invoke(main, ["docs", "init", "--path", fs])
        assert init_result.exit_code == 0

        doc_file = Path(fs) / "deploy.md"
        doc_file.write_text("Run pytest before deploying.", encoding="utf-8")

        add_result = runner.invoke(main, [
            "docs", "add", "master",
            "--title", "API Deploy",
            "--author", "alice",
            "--type", "how-to",
            "--tags", "api,deploy",
            "--file", str(doc_file),
            "--config", fs,
        ])
        assert add_result.exit_code == 0

        search_result = runner.invoke(main, [
            "docs", "search", "pytest",
            "--mode", "keyword",
            "--config", fs,
        ])
        assert search_result.exit_code == 0
        assert "Found" in search_result.output


def test_mcp_tool_full_workflow(tmp_path):
    config = DocHubConfig({"name": "test-kb"}, base_path=tmp_path)
    tool = DocHubTool(config)

    tool.run("doc_create", {
        "title": "API Deploy",
        "content": "Run pytest before deploy.",
        "author": "alice",
        "doc_type": "how-to",
        "tags": ["api"],
    })
    tool.run("doc_add_addendum", {
        "parent_doc_id": "api_deploy",
        "contributor": "bob",
        "content": "Use docker compose up.",
        "summary": "Docker deploy",
    })

    result = tool.run("doc_search", {"query": "docker", "mode": "keyword"})
    assert result["total"] >= 1

    read = tool.run("doc_read", {"doc_id": "api_deploy"})
    assert "bob" in read["addendums"]
