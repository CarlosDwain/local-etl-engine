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

## Generate synthetic source data

The generator creates Excel workbooks and `ground_truth.json` in a new or empty output directory.
Use separate directories for the benchmark sizes:

```
uv run python tools\generate_data.py --rows 100000 --seed 42 --profile clean --output-dir data\synthetic\clean-100k
uv run python tools\generate_data.py --rows 1000000 --seed 42 --profile clean --output-dir data\synthetic\clean-1m
uv run python tools\generate_data.py --rows 5000000 --seed 42 --profile clean --output-dir data\synthetic\clean-5m
uv run python tools\generate_data.py --rows 100000 --seed 42 --profile messy --output-dir data\synthetic\messy-100k
```

The clean profile is intended for timing runs. The messy profile injects the error and schema-drift
cases listed in `ground_truth.json` for behavior tests. Generated files are synthetic and excluded
from version control by `.gitignore`.

## Legacy read-stage benchmark

The optional legacy baseline measures a limited ingestion path: Excel read, the legacy no-op
transform path, and SQLite database/schema setup and load for synthetic GL input. It is not an
end-to-end ETL comparison. Generate the clean 100K and 1M datasets first, then copy only the legacy
backend's `src` folder into a local, isolated sandbox under
`%LOCALAPPDATA%\FIA-ETL-Benchmark\legacy`; do not copy its data or use its existing configuration.
The benchmark runner writes sanitized configuration into that copy and creates a fresh SQLite
database for every run.

```
$benchmarkRoot = Join-Path $env:LOCALAPPDATA "FIA-ETL-Benchmark"
$legacySource = "C:\path\to\FIA Backend ETL"
$legacySandbox = Join-Path $benchmarkRoot "legacy"
New-Item -ItemType Directory -Path $legacySandbox
Copy-Item -LiteralPath (Join-Path $legacySource "src") -Destination $legacySandbox -Recurse
New-Item -ItemType Directory -Path (Join-Path $legacySandbox "resources\configuration")

uv run python -m tools.benchmark_legacy_read `
  --benchmark-root $benchmarkRoot `
  --legacy-python "$env:LOCALAPPDATA\anaconda3\envs\OTC_venv2\python.exe" `
  --conda-executable "$env:LOCALAPPDATA\anaconda3\Scripts\conda.exe" `
  --conda-environment OTC_venv2
```

The runner records input hashes, environment details, per-run timings and row counts, summary
statistics, and subprocess logs outside the repository. The completed legacy-only baseline is
summarized in [benchmarks/legacy-read/README.md](./benchmarks/legacy-read/README.md); it is not an
end-to-end comparison, and the Step 3 comparison is still pending.

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
