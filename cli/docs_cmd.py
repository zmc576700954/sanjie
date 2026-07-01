"""agents-dev docs subcommand group for DocHub."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from agents_dev.docs.config import DocHubConfig
from agents_dev.docs.mcp.tools import DocHubTool

console = Console()


def _load_config(path: Path) -> DocHubConfig:
    yaml_path = Path(path) / "dochub.yaml"
    if not yaml_path.exists():
        raise click.ClickException(f"No dochub.yaml found at {yaml_path}")
    return DocHubConfig.from_yaml(yaml_path)


@click.group("docs")
def docs_cmd() -> None:
    """Manage the DocHub knowledge base."""


@docs_cmd.command("init")
@click.option("--path", "-p", default=".", help="Path to initialize the knowledge base")
def init_cmd(path: str) -> None:
    """Initialize a new DocHub knowledge base."""
    base = Path(path)
    base.mkdir(parents=True, exist_ok=True)
    (base / "docs" / "master").mkdir(parents=True, exist_ok=True)
    (base / "docs" / "addendums").mkdir(parents=True, exist_ok=True)
    (base / "index").mkdir(parents=True, exist_ok=True)
    (base / "sessions").mkdir(parents=True, exist_ok=True)

    config_path = base / "dochub.yaml"
    if not config_path.exists():
        config_path.write_text(
            "name: dochub\nversion: \"1.0.0\"\n"
            "index:\n  keyword:\n    backend: sqlite\n"
            "chunking:\n  size: 512\n  overlap: 100\n"
            "search:\n  default_mode: keyword\n  top_k: 10\n",
            encoding="utf-8",
        )

    console.print(f"[green]Initialized DocHub at[/green] {base.absolute()}")


@docs_cmd.command("add")
@click.argument("kind", type=click.Choice(["master"]))
@click.option("--title", required=True, help="Document title")
@click.option("--author", required=True, help="Document author")
@click.option("--type", "doc_type", required=True, type=click.Choice(["tutorial", "how-to", "reference", "explanation"]))
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--session-id", default=None, help="Session ID")
@click.option("--summary", default=None, help="Document summary")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="Markdown file to ingest")
@click.option("--config", "-c", default=".", help="Path to DocHub base directory")
def add_cmd(
    kind: str,
    title: str,
    author: str,
    doc_type: str,
    tags: str,
    session_id: Optional[str],
    summary: Optional[str],
    file_path: str,
    config: str,
) -> None:
    """Add a master document to the knowledge base."""
    cfg = _load_config(config)
    tool = DocHubTool(cfg)
    content = Path(file_path).read_text(encoding="utf-8")
    result = tool.run("doc_create", {
        "title": title,
        "content": content,
        "author": author,
        "doc_type": doc_type,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "session_id": session_id,
        "summary": summary,
    })
    console.print(f"[green]Created {kind} document[/green] {result['doc_id']}")


@docs_cmd.command("search")
@click.argument("query")
@click.option("--mode", default="keyword", type=click.Choice(["keyword", "semantic", "hybrid"]))
@click.option("--author", default=None)
@click.option("--contributor", default=None)
@click.option("--session-id", default=None)
@click.option("--doc-type", default=None)
@click.option("--limit", default=10, type=int)
@click.option("--config", "-c", default=".")
def search_cmd(
    query: str,
    mode: str,
    author: Optional[str],
    contributor: Optional[str],
    session_id: Optional[str],
    doc_type: Optional[str],
    limit: int,
    config: str,
) -> None:
    """Search the DocHub knowledge base."""
    cfg = _load_config(config)
    tool = DocHubTool(cfg)
    filters = {
        "author": author,
        "contributor": contributor,
        "session_id": session_id,
        "doc_type": doc_type,
        "limit": limit,
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    result = tool.run("doc_search", {"query": query, "mode": mode, "filters": filters, "limit": limit})
    console.print(f"Found {result['total']} results for '{result['query']}'")
    for chunk in result["chunks"]:
        console.print(f"- [bold]{chunk['doc_title']}[/bold] ({chunk['doc_type']})")
        console.print(f"  {chunk['content'][:200]}...")


@docs_cmd.command("ask")
@click.argument("question")
@click.option("--session-id", default=None)
@click.option("--config", "-c", default=".")
def ask_cmd(question: str, session_id: Optional[str], config: str) -> None:
    """Ask a question using RAG over the knowledge base."""
    cfg = _load_config(config)
    tool = DocHubTool(cfg)
    filters = {"session_id": session_id} if session_id else {}
    result = tool.run("doc_query", {"question": question, "filters": filters})
    console.print("[bold]Generated prompt for LLM:[/bold]")
    console.print(result["prompt"])


@docs_cmd.command("serve")
@click.option("--config", "-c", default=".", help="Path to DocHub base directory")
@click.option("--transport", default="stdio", type=click.Choice(["stdio"]))
def serve_cmd(config: str, transport: str) -> None:
    """Start the DocHub MCP server."""
    cfg = _load_config(config)
    if transport != "stdio":
        raise click.ClickException("Only stdio transport is supported")
    console.print(f"[green]Starting DocHub MCP server[/green] ({cfg.base_path})")
    from agents_dev.docs.mcp.server import DocHubMCPServer
    server = DocHubMCPServer(cfg)
    console.print(f"Server info: {server.get_server_info()}")
    console.print(
        "[yellow]DocHub MCP server is ready.[/yellow]\n"
        "The server exposes tools via the MCP protocol. In a production setup,\n"
        "this would run as a long-lived stdio or SSE transport process.\n"
        "For now, use the generated MCP format files (see formats/dochub/) to\n"
        "wire the server into your MCP client."
    )
