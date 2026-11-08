"""Persist incremental manifest entries in a small DuckDB file."""

import contextlib
from datetime import datetime
from pathlib import Path

import duckdb

from etl.domain.manifest import FileStatus, ManifestEntry


class DuckDbManifestStore:
    def __init__(self, database: Path) -> None:
        database.parent.mkdir(parents=True, exist_ok=True)
        self._connection = duckdb.connect(str(database))
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS manifest ("
            "path VARCHAR PRIMARY KEY, content_hash VARCHAR, contract_hash VARCHAR, "
            "status VARCHAR, processed_at VARCHAR, layout_hash VARCHAR DEFAULT '')"
        )
        with contextlib.suppress(duckdb.CatalogException):
            self._connection.execute(
                "ALTER TABLE manifest ADD COLUMN layout_hash VARCHAR DEFAULT ''"
            )

    def get(self, path: str) -> ManifestEntry | None:
        row = self._connection.execute(
            "SELECT content_hash, contract_hash, status, processed_at, layout_hash "
            "FROM manifest WHERE path = ?",
            [path],
        ).fetchone()
        if row is None:
            return None
        return ManifestEntry(
            path=path,
            content_hash=str(row[0]),
            contract_hash=str(row[1]),
            status=FileStatus(str(row[2])),
            processed_at=datetime.fromisoformat(str(row[3])),
            layout_hash=str(row[4]),
        )

    def upsert(self, entry: ManifestEntry) -> None:
        self._connection.execute(
            "INSERT INTO manifest VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(path) DO UPDATE SET content_hash = excluded.content_hash, "
            "contract_hash = excluded.contract_hash, status = excluded.status, "
            "processed_at = excluded.processed_at, layout_hash = excluded.layout_hash",
            [
                entry.path,
                entry.content_hash,
                entry.contract_hash,
                entry.status.value,
                entry.processed_at.isoformat(),
                entry.layout_hash,
            ],
        )

    def close(self) -> None:
        self._connection.close()
