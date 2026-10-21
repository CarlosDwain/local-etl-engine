# Copilot instructions: modern local ETL (DuckDB + Parquet)

This is a layered, ports-and-adapters Python project. These rules apply to **every** request.

## Before you write any code

1. Read `docs/build-plan.md`. Work only on the current step unless told otherwise.
2. Read the standards that apply to the files you will touch:
   - Layering and where code goes: `docs/standards/architecture.md`
   - Python style: `docs/standards/coding-standards.md`
   - Layers, contracts, Parquet, lineage: `docs/standards/data-standards.md`
   - Errors and results: `docs/standards/error-handling.md`
   - Tests: `docs/standards/testing-standards.md`
3. Path-specific rules in `.github/instructions/` load automatically. Follow them.
4. If a request conflicts with a rule, name the rule by its ID (for example `A-4`), propose a
   compliant alternative, and ask before breaking it. Never break a rule silently.

## Non-negotiables (full text in the standards)

- **Dependencies point inward** (A-1): `interfaces -> application -> domain`; `infrastructure`
  implements `application/ports.py`. `domain` and `application` never import DuckDB, Excel
  libraries, YAML, Pydantic, Tkinter, or Typer.
- **Only `container.py` constructs adapters** (A-4). Pass dependencies through constructors. No globals.
- **No new abstraction without a realistic second implementation** (A-7). Otherwise ask first.
- **Everything is typed**, `mypy --strict` clean (C-1). Domain objects are frozen dataclasses (C-3).
- **No `print`, no relative imports, no wildcard or dynamic imports** (C-5, C-10).
- **SQL lives in `sql/*.sql`**, parameterized, never built from f-strings (C-12).
- **No hardcoded paths or thresholds** (C-11). Read config or contracts.
- **Expected failures are returned as results, not raised** (E-1). Unexpected ones raise `EtlError` subclasses.
- **Never use real client data.** Fixtures and samples are synthetic only (D-14).
- **Parquet writes are atomic** (D-8). Partition replacement, never in-place edits.

## After you write code

1. Add or update tests (`docs/standards/testing-standards.md`). Fakes for unit tests, real adapters only in `tests/integration/`.
2. Run `python scripts/check.py`. Fix every failure. Do not weaken a rule or a test to make it pass.
3. Walk the checklist in `docs/standards/definition-of-done.md`.
4. In your reply, list the rule IDs that shaped the change and anything the human should review.

## When unsure

Ask. Do not invent folders, ports, dependencies, or file formats that are not in the standards. If a
significant design decision is needed, draft an ADR in `docs/adr/` using the template instead of
deciding inside code.

## Tooling

`uv sync` to install, `uv run python scripts/check.py` for all gates. Python 3.12. Windows is the
target platform, so use `pathlib`, never hardcode `/` or `\`.
