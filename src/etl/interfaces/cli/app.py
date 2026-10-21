"""Command-line interface. Thin: builds the runner through the container and calls it (A-10)."""

from pathlib import Path
from typing import Annotated

import typer

from etl import __version__
from etl.application.stages.base import RunOptions
from etl.config import load_config
from etl.container import build_runner
from etl.domain.errors import EtlError
from etl.domain.period import Period

app = typer.Typer(help="Modern local ETL tool.", no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the version."""
    typer.echo(__version__)


@app.command()
def run(
    config: Annotated[Path, typer.Option(help="Path to config.yaml")] = Path("config.yaml"),
    full_refresh: Annotated[bool, typer.Option("--full-refresh")] = False,
    source: Annotated[list[str] | None, typer.Option("--source", help="Limit to a source")] = None,
    period_from: Annotated[str | None, typer.Option("--from", help="YYYY-MM")] = None,
    period_to: Annotated[str | None, typer.Option("--to", help="YYYY-MM")] = None,
) -> None:
    """Run the pipeline."""
    try:
        runner = build_runner(load_config(config))
        options = RunOptions(
            full_refresh=full_refresh,
            sources=tuple(source or ()),
            period_from=Period.parse(period_from) if period_from else None,
            period_to=Period.parse(period_to) if period_to else None,
        )
        summary = runner.run(options)
    except (EtlError, ValueError) as error:
        typer.echo(f"Error: {error}")
        raise typer.Exit(code=1) from error
    typer.echo(
        f"Done. stages={len(summary.results)} rejected={summary.rows_rejected} "
        f"files_failed={summary.files_failed}"
    )
    if not summary.ok:
        typer.echo(f"Run stopped: {summary.error}")
        raise typer.Exit(code=1)
