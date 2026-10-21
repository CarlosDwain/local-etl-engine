# ADR 0002: DuckDB engine with Parquet storage

- Status: accepted

## Context
SQLite is a row store and is slow for analytical work at 1M+ rows. Excel is slow to parse repeatedly.
No budget for cloud or paid services; confidential data must stay local.

## Decision
DuckDB (embedded, free, columnar) as the engine. Parquet as the storage format for raw, staging, and
marts. Excel only at the edges: read once into raw, written at export.

## Consequences
Fast joins and aggregations, small files, open formats Power BI can read. DuckDB files allow a single
writer and must not live in synced folders (rule D-12). Parquet cannot be edited in place, so changes
replace whole partitions (rule D-8).
