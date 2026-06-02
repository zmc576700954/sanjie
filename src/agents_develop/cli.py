"""CLI entry point for agents-develop."""
import json
import click

from .config import Config
from .llm_client import LLMClient
from .orchestrator import Orchestrator
from .schemas import InvestigateInput, FixInput, ReviewInput, DocumentInput, TokenBudget


def _get_orchestrator(budget_total: int = 200_000) -> Orchestrator:
    config = Config.load()
    llm = LLMClient(provider=config.provider, model=config.model, api_key=config.api_key)
    budget = TokenBudget(total=budget_total)
    return Orchestrator(llm, token_budget=budget)


@click.group()
@click.version_option(package_name="agents-develop")
def main():
    """AI-powered code investigation, fixing, and review toolkit."""
    pass


@main.command()
@click.argument("error_description")
@click.option("--file", "files", multiple=True, help="Source files related to the error.")
@click.option("--log", "log_file", default=None, help="Path to log file.")
@click.option("--budget", default=200_000, type=int, help="Token budget for the operation.")
def investigate(error_description, files, log_file, budget):
    """Investigate an error and find root cause."""
    orch = _get_orchestrator(budget)
    input_data = InvestigateInput(
        error_description=error_description,
        source_files=list(files),
        log_file=log_file,
    )
    result = orch.investigate(input_data)
    click.echo(result.model_dump_json(indent=2))
    click.echo(f"\n[Token budget: {orch.token_budget.spent}/{orch.token_budget.total} used]")


@main.command()
@click.argument("error_description")
@click.option("--file", "files", multiple=True, required=True, help="Files to fix.")
@click.option("--review", is_flag=True, help="Run review after fixing.")
@click.option("--safety", default="standard", type=click.Choice(["strict", "standard", "aggressive"]))
@click.option("--budget", default=200_000, type=int, help="Token budget for the operation.")
def fix(error_description, files, review, safety, budget):
    """Investigate and fix a bug."""
    orch = _get_orchestrator(budget)
    input_data = FixInput(
        error_description=error_description,
        target_files=list(files),
        safety_level=safety,
    )
    if review:
        result = orch.fix_and_review(input_data)
        click.echo(json.dumps({
            "fix": result["fix"].model_dump() if result["fix"] else None,
            "review": result["review"].model_dump() if result["review"] else None,
            "error": result.get("error"),
            "stages": result.get("stages", []),
        }, indent=2))
    else:
        result = orch.fix(input_data)
        click.echo(result.model_dump_json(indent=2))
    click.echo(f"\n[Token budget: {orch.token_budget.spent}/{orch.token_budget.total} used]")


@main.command()
@click.argument("path")
@click.option("--type", "review_types", multiple=True,
              type=click.Choice(["format", "security", "quality"]),
              default=["format", "security", "quality"],
              help="Review types to run.")
@click.option("--budget", default=200_000, type=int, help="Token budget for the operation.")
def review(path, review_types, budget):
    """Review code for security, quality, and format compliance."""
    orch = _get_orchestrator(budget)
    input_data = ReviewInput(target_path=path, review_types=list(review_types))
    result = orch.review(input_data)
    click.echo(result.model_dump_json(indent=2))
    click.echo(f"\n[Token budget: {orch.token_budget.spent}/{orch.token_budget.total} used]")


@main.command()
@click.argument("task_description")
def route(task_description):
    """Route a task to the best matching skill.

    Shows which skill would handle the task based on keyword matching,
    per SPEC.md section 4.4 routing decision flow.
    """
    orch = _get_orchestrator()
    skill = orch.route_task(task_description)
    if skill:
        click.echo(json.dumps({
            "matched_skill": skill.name,
            "description": skill.description,
            "tools": skill.tools,
            "module_path": skill.module_path,
        }, indent=2))
    else:
        click.echo("No matching skill found for this task.")


@main.command()
@click.argument("source_paths", nargs=-1, required=True)
@click.option("--doc-type", default="spec",
              type=click.Choice(["spec", "archive", "handoff", "memory"]),
              help="Document type to generate.")
@click.option("--output", "output_path", default=None, help="Output file path.")
@click.option("--budget", default=200_000, type=int, help="Token budget for the operation.")
def document(source_paths, doc_type, output_path, budget):
    """Generate structured documentation using the GSSC pipeline.

    Bridges to the Taibai skill for documentation generation.
    """
    orch = _get_orchestrator(budget)
    input_data = DocumentInput(
        source_paths=list(source_paths),
        doc_type=doc_type,
    )
    result = orch.document(input_data)
    click.echo(result.model_dump_json(indent=2))
    click.echo(f"\n[Token budget: {orch.token_budget.spent}/{orch.token_budget.total} used]")


@main.command()
@click.argument("error_description")
@click.option("--file", "files", multiple=True, required=True, help="Files to process.")
@click.option("--safety", default="standard", type=click.Choice(["strict", "standard", "aggressive"]))
@click.option("--budget", default=200_000, type=int, help="Token budget for the operation.")
def pipeline(error_description, files, safety, budget):
    """Run the full pipeline: investigate → fix → review with tracing.

    Returns a PipelineResult with all stage results, handoff history,
    and token usage across the entire pipeline.
    """
    orch = _get_orchestrator(budget)
    input_data = FixInput(
        error_description=error_description,
        target_files=list(files),
        safety_level=safety,
    )
    result = orch.full_pipeline(input_data)
    click.echo(result.model_dump_json(indent=2))


@main.group()
def config():
    """Manage configuration."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = Config.load()
    data = {"provider": cfg.provider, "model": cfg.model}
    click.echo(json.dumps(data, indent=2))


@config.command("set-provider")
@click.argument("value")
def config_set_provider(value):
    """Set LLM provider (anthropic or openai)."""
    cfg = Config.load()
    cfg.set_value("provider", value)
    click.echo(f"Provider set to: {value}")


@config.command("set-key")
@click.argument("value")
def config_set_key(value):
    """Set API key."""
    cfg = Config.load()
    cfg.set_value("key", value)
    click.echo("API key saved.")


@config.command("set-model")
@click.argument("value")
def config_set_model(value):
    """Set model name."""
    cfg = Config.load()
    cfg.set_value("model", value)
    click.echo(f"Model set to: {value}")
