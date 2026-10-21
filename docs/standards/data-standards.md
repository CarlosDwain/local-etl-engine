# Data standards

## Layers (medallion)

| Layer | Also called | Contents |
|---|---|---|
| raw | bronze | Faithful copy of the source, all columns as text, canonical names, lineage columns |
| staging | silver | Typed, cleaned, deduplicated, validated, one table per source; rejects set aside |
| marts | gold | Business logic, joins, aggregations for reporting and output |

- **D-1 Every layer reads only from the one before it.**
- **D-2 Marts never read raw; staging never reads Excel.**
- **D-3 Raw has no business decisions.** Rename, add lineage, write Parquet. Nothing else.

## Storage

```
<working>/data/
├── raw/<source>/period=YYYY-MM/part-<filehash8>.parquet
├── staging/<source>/period=YYYY-MM/part-0.parquet
├── staging/_rejects/<source>/period=YYYY-MM/rejects.parquet
├── marts/<mart>/period=YYYY-MM/part-0.parquet     # small marts may be a single file
└── archive/<source>/period=YYYY-MM/<timestamp>/   # later
<working>/state/   manifest and run log
<working>/logs/    text logs
```

- **D-4 Parquet with zstd compression,** Hive-style `period=YYYY-MM` partitions, row groups of about 100K to 1M rows.
- **D-5 Excel is read as text.** Typing happens in staging with `TRY_CAST`. Reading never fails on a bad value.
- **D-6 Lineage columns on every row:** `_source_file`, `_sheet`, `_row_number`, `_file_hash`, `_ingested_at`, plus `period`. SQL must carry them through staging.
- **D-7 Table naming:** `stg_<source>`, `dim_<name>`, `fact_<name>`, `mart_<name>`. Columns are `snake_case`.
- **D-8 Writes are atomic.** Write to a temp directory, then swap the partition in. Never edit Parquet in place; replace the partition.

## Contracts

- **D-9 One YAML contract per source** in `contracts/`, shared settings in `_defaults.yaml`. Validated by Pydantic at startup so a bad contract fails fast.
- **D-10 Business key.** Every contract declares `keys` (the columns that uniquely identify a row in business terms) or `key_strategy: generated` (hash of meaningful columns plus an occurrence counter).
- **D-11 Versioning.** Git is the version history. The `version` field and per-period `layouts` (later) support reprocessing history. The manifest stores the contract hash used for each file.
- Declare the columns we use, required or optional. Unknown columns follow `extra_columns: drop | warn | keep`.
- Columns match by header name or alias. Order does not matter. The header row position matters.

## Drift policy

| Change in file | Behavior |
|---|---|
| Required column missing or renamed | File fails with a clear message, other files continue |
| Known alias present | Treated as the same column |
| Unknown column | Warn, ignore (or keep in raw, per `extra_columns`) |
| Header row moved | Usually shows as missing columns, fails with a message |
| Value of the wrong type | Not drift. Caught by `TRY_CAST` in staging, goes to rejects |

## Working folders

- **D-12 The working folder is local and automatic:** `%LOCALAPPDATA%\<ToolName>\data`. Validate on launch: exists, writable, not inside OneDrive or SharePoint sync. The `.duckdb` file and Parquet working data never live in a synced folder. Only final outputs go to synced folders.
- **D-13 Incremental processing.** File level (skip unchanged by hash and modified time, via the manifest) plus partition level (replace only the affected `period=`). Always support `--full-refresh`.
- **D-14 Synthetic data only** in the repo, tests, and samples. No real client data, ever. `.gitignore` blocks data files; do not work around it.
- **D-15 Schema evolution.** Staging follows the current canonical schema. Older partitions that lack a column read as `NULL` (`union_by_name=true`) unless the contract declares a default.
