---
applyTo: "src/etl/application/**"
---
# Application layer rules

- Depend only on `etl.domain` and `etl.application.ports` (A-3). Never import DuckDB, openpyxl,
  calamine, xlsxwriter, Tkinter, Typer, YAML, or Pydantic.
- Ports in `ports.py` are small `typing.Protocol` classes (A-5). One job per port.
- Stages subclass `Stage` and implement `plan` and `execute` only. Do not override `run` (A-8).
- Return `StageResult` objects for expected outcomes; raise `EtlError` subclasses for unexpected failures (E-1, E-2).
- Constructors receive ports. Never instantiate an adapter here (A-4).
- Report progress through `ProgressReporter` between steps, never per row.
- Quality checks are small classes combined by `QualityGate`; do not grow one giant check.
