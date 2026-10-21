"""QueryEngine backed by embedded DuckDB."""

from collections.abc import Mapping

import duckdb


class DuckDbEngine:
    def __init__(self, database: str = ":memory:") -> None:
        self._connection = duckdb.connect(database)

    def execute(self, sql: str, params: Mapping[str, object] | None = None) -> None:
        self._connection.execute(sql, dict(params) if params else None)

    def fetch_all(
        self, sql: str, params: Mapping[str, object] | None = None
    ) -> list[tuple[object, ...]]:
        return self._connection.execute(sql, dict(params) if params else None).fetchall()

    def close(self) -> None:
        self._connection.close()
