# Modern local ETL (DuckDB + Parquet)

A learning project showing a modern alternative to our SQLite/Excel ETL tool. Local only, free, fast
at 1M+ rows, layered so each tool can be swapped. The architecture is part of the deliverable.

## Quick start

```
uv sync
uv run python scripts/check.py     # ruff, format, mypy --strict, import-linter, pytest
uv run pre-commit install          # optional: run the gates on every commit
uv run etl --help
```

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

## Working with Copilot (VS Code agent mode)

The rules are written for the agent to follow automatically.

- `.github/copilot-instructions.md` loads on every request. It points at the standards.
- `.github/instructions/*.instructions.md` load by file path (domain, application, SQL, tests, ...).
- `.github/prompts/*.prompt.md` are reusable tasks. In Copilot Chat type `/new-stage`,
  `/new-port-and-adapter`, `/new-source-contract`, or `/review-against-standards`.
- `AGENTS.md` points other agents to the same rules.
- Ask for **one build step at a time** from `docs/build-plan.md`.

If the agent seems to ignore the rules, open Copilot Chat's "References" for the reply and check that
`copilot-instructions.md` is listed. VS Code setting names for instruction files change between
versions; `.vscode/settings.json` has the current ones, so verify them in Settings if needed.

## Layout

```
.github/        Copilot rules, path-specific instructions, reusable prompts
docs/           standards (A-*, C-*, D-*, E-*, T-*), build plan, ADRs
contracts/      one YAML per data source (+ _defaults.yaml)
sql/            staging and mart SQL, one SELECT per file
src/etl/        domain, application, infrastructure, interfaces, container, config
tests/          unit (fakes) and integration (real adapters)
tools/          synthetic data generator
scripts/        check.py (all quality gates)
```

## Status

See `docs/build-plan.md`. The scaffold compiles, passes every gate, and stubs the rest as `TODO(step N)`.
