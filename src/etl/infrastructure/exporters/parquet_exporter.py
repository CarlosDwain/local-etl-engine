"""Export a DuckDB table to compressed Parquet."""

from pathlib import Path

from etl.application.ports import QueryEngine


class ParquetExporter:
    def __init__(self, engine: QueryEngine) -> None:
        self._engine = engine

    def export(self, table: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._engine.copy_relation(table, dest)
        return dest
