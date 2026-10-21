# Coding standards

- **C-1 Type everything.** `mypy --strict` must pass. No `Any` unless justified in a comment.
- **C-2 Ruff clean.** Lint and format with ruff. Line length 100.
- **C-3 Domain objects are frozen dataclasses.** Immutable, validated in `__post_init__`.
- **C-4 Pydantic only at boundaries.** YAML contract parsing and config validation in `infrastructure/contracts` or `config.py`, then map to domain dataclasses.
- **C-5 No `print`.** Use `logging` for diagnostics and `typer.echo` / the reporter for user output.
- **C-6 Use `pathlib.Path`,** never string paths, never hardcoded separators. Windows is the target.
- **C-7 Naming.** `snake_case` functions and modules, `PascalCase` classes, `UPPER_CASE` constants. Adapters are named after the technology, ports after the role.
- **C-8 Docstrings explain why,** not what. Public classes and non-trivial functions get one.
- **C-9 Keep functions small** (about 40 lines). One class, one job.
- **C-10 Imports are absolute and explicit.** No relative imports, no wildcard imports, no dynamic imports or plugin auto-discovery (PyInstaller cannot see them).
- **C-11 No hardcoded paths or thresholds.** They come from `config.yaml` or contracts.
- **C-12 SQL lives in `sql/*.sql` files,** parameterized. Never build SQL with f-strings from user or file data. Identifiers that must vary come from validated contract names only.
- **C-13 Time is UTC and timezone-aware.** `datetime.now(UTC)`. Inject a clock where tests need determinism.
- **C-14 No mutable default arguments.** No bare `except`. Catch specific exceptions.
- **C-15 TODO format:** `TODO(step N): description`, where N is the step in `docs/build-plan.md`.
- **C-16 Dependencies:** add a library only when needed and note why in the PR or an ADR. Do not use pandas in `domain/` or `application/`.

## Commands

```
uv sync                              # install
uv run python scripts/check.py       # all gates: ruff, format, mypy, import-linter, pytest
uv run ruff check --fix . && uv run ruff format .
uv run pre-commit install            # run gates on each commit
```
