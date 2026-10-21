---
applyTo: "src/etl/infrastructure/**"
---
# Infrastructure layer rules

- Each class implements exactly one port from `application/ports.py`. Name classes after the
  technology (`DuckDbEngine`, `CalamineExcelReader`), name ports after the role.
- May import `domain` and `application.ports`. Never `interfaces` or `container` (A-1).
- Pydantic and YAML parsing live here (`infrastructure/contracts`), mapped into domain dataclasses at the boundary (C-4).
- Parquet writes go to a temp directory first, then swap in atomically (D-8).
- DuckDB: use `TRY_CAST`, `read_parquet(..., hive_partitioning=true)`, `union_by_name=true`; write Parquet
  with zstd. Always pass parameters, never string-build SQL (C-12).
- Read Excel values as text first; typing happens in staging SQL (D-5).
- No dynamic imports or plugin discovery (C-10): PyInstaller cannot see them.
