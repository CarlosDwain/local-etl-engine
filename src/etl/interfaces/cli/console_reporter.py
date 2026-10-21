"""ProgressReporter that writes to the console."""

import typer


class ConsoleReporter:
    def update(self, step: str, fraction: float) -> None:
        typer.echo(f"[{fraction:>4.0%}] {step}")
