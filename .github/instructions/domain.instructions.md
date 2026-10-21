---
applyTo: "src/etl/domain/**"
---
# Domain layer rules

- Pure Python only: dataclasses, enums, `pathlib`, `datetime`, `re`, `typing`. No file reads, no network.
- Frozen dataclasses with `slots` where sensible (C-3). Validate in `__post_init__` and raise `EtlError` subclasses.
- No imports from `application`, `infrastructure`, `interfaces`, `container`, `config`, or any
  third-party I/O library (A-2). `import-linter` enforces this.
- Value objects (`Period`, `Layer`) and result types (`StageResult`, `RunSummary`) live here.
- Keep behaviour that belongs to a concept on that concept (for example `Contract` checks its own keys).
