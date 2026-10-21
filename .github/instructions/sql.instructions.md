---
applyTo: "sql/**"
---
# SQL rules

- One `SELECT` per file. The file name is the table name: `stg_<source>.sql`, `fact_*.sql`, `dim_*.sql`, `mart_*.sql`.
- Start each file with a header comment declaring `-- depends_on: <table>, <table>` so the runner (and later dbt `ref()`) can order models.
- Staging casts with `TRY_CAST` and keeps lineage columns (`_source_file`, `_sheet`, `_row_number`, `_file_hash`, `_ingested_at`, `period`) (D-6).
- Marts read only from staging or other marts, never raw (D-2).
- snake_case column names, explicit column lists (no `SELECT *` in marts), no business logic hidden in Python.
