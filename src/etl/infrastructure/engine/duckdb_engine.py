"""QueryEngine backed by embedded DuckDB."""

from collections.abc import Mapping
from pathlib import Path

import duckdb


class DuckDbEngine:
    def __init__(self, database: str = ":memory:") -> None:
        if database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
        self._connection = duckdb.connect(database)

    def execute(self, sql: str, params: Mapping[str, object] | None = None) -> None:
        self._connection.execute(sql, dict(params) if params else None)

    def fetch_all(
        self, sql: str, params: Mapping[str, object] | None = None
    ) -> list[tuple[object, ...]]:
        return self._connection.execute(sql, dict(params) if params else None).fetchall()

    def copy_relation(self, relation: str, destination: Path) -> None:
        self._connection.execute(
            "COPY (SELECT * FROM " + relation + ") TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
            [str(destination)],
        )

    def close(self) -> None:
        self._connection.close()
