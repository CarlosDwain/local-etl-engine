# Architecture standards

Layered ports-and-adapters (hexagonal). The business logic knows nothing about tools.

```
interfaces ──► application ──► domain
                   ▲
infrastructure ────┘   (implements application/ports.py)
container.py wires them together
```

## Rules

- **A-1 Dependencies point inward.** `interfaces -> application -> domain`. `infrastructure` implements ports and never imports `interfaces` or `container`.
- **A-2 Domain is pure.** No I/O, no third-party I/O libraries (DuckDB, YAML, Pydantic, Tkinter, Typer, Excel libraries).
- **A-3 Application depends only on domain and ports.** It never imports an adapter or a tool.
- **A-4 Only `container.py` constructs adapters.** Everything else receives dependencies through constructors. No globals, no hidden singletons.
- **A-5 Ports are small `typing.Protocol` classes.** One job each (interface segregation). Names describe the role.
- **A-6 Adapters are named after the technology** (`DuckDbEngine`) and implement exactly one port each.
- **A-7 No abstraction without a realistic second implementation.** If you cannot name one, write the plain version. Real seams in this project: file source (local / Graph), reader (Excel / CSV), exporter (Excel / Parquet), reporter (console / Tkinter), engine and stores (real / fake in tests).
- **A-8 Stages use the template method.** `Stage.run` = `plan -> execute -> validate -> commit`. Subclasses implement `plan` and `execute`; they do not override `run`.
- **A-9 Prefer composition over inheritance.** Inherit only for the `Stage` template. Combine small `Check` objects with `QualityGate`.
- **A-10 Interfaces call the application through the container.** CLI and Tkinter never import `etl.infrastructure`.
- **A-11 The runner never knows which UI called it.** Progress goes through `ProgressReporter`.

These are enforced mechanically by `import-linter` (see `pyproject.toml`). A failing `lint-imports` is a real architecture violation, not noise.

## Where does this code go?

| I am writing... | Put it in |
|---|---|
| A concept with rules (`Contract`, `Period`) | `domain/` |
| A result type or error | `domain/results.py`, `domain/errors.py` |
| "Something must read / write / run X" (an interface) | `application/ports.py` |
| What the pipeline does and in which order | `application/` (stages, runner) |
| Code that talks to DuckDB, Excel, files, YAML | `infrastructure/` |
| A CLI command or Tkinter window | `interfaces/` |
| Choosing which adapters to use | `container.py` |
| Reading `config.yaml` | `config.py` |
| Transformation logic | `sql/` |

## Patterns in use

Template method (stages), strategy (key generation, drift policy), composition (checks), observer (progress reporter), repository (manifest, run log), registry by explicit import (readers, exporters), MVP (Tkinter).

## Design decisions

Record significant ones as ADRs in `docs/adr/`.
