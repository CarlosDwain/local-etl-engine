"""Atomically store one Parquet partition per source period."""

import shutil
import uuid
from collections.abc import Sequence
from pathlib import Path

import duckdb

from etl.application.ports import QueryEngine
from etl.domain.layer import Layer
from etl.domain.period import Period


class ParquetLayerStore:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def write_rows(
        self,
        layer: Layer,
        table: str,
        period: Period,
        columns: Sequence[str],
        rows: Sequence[Sequence[str | None]],
    ) -> None:
        if not rows:
            return
        target = self._partition_path(layer, table, period)
        temp_dir = target.parent / f".{target.name}.tmp-{uuid.uuid4().hex}"
        temp_dir.mkdir(parents=True)
        try:
            temp_file = temp_dir / "part.parquet"
            connection = duckdb.connect()
            try:
                column_sql = ", ".join(f'"{column}" VARCHAR' for column in columns)
                connection.execute(f"CREATE TABLE staged ({column_sql})")
                placeholders = ", ".join("?" for _ in columns)
                connection.executemany(f"INSERT INTO staged VALUES ({placeholders})", rows)
                connection.execute(
                    "COPY staged TO ? (FORMAT PARQUET, COMPRESSION ZSTD)", [str(temp_file)]
                )
            finally:
                connection.close()
            _atomic_replace(temp_file, target / "part-0.parquet")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def list_partitions(self, layer: Layer, table: str) -> list[Period]:
        table_dir = self._data_dir / layer.value / table
        if not table_dir.is_dir():
            return []
        return sorted(
            Period.parse(path.name.removeprefix("period="))
            for path in table_dir.glob("period=*")
            if path.is_dir()
        )

    def export_relation(
        self,
        layer: Layer,
        table: str,
        period: Period,
        relation: str,
        engine: QueryEngine,
    ) -> None:
        target = self._partition_path(layer, table, period)
        temp_dir = target.parent / f".{target.name}.tmp-{uuid.uuid4().hex}"
        temp_dir.mkdir(parents=True)
        try:
            temp_file = temp_dir / "part.parquet"
            engine.copy_relation(relation, temp_file)
            _atomic_replace(temp_file, target / "part-0.parquet")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _partition_path(self, layer: Layer, table: str, period: Period) -> Path:
        return self._data_dir / layer.value / table / period.partition_dir


def _atomic_replace(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    replacement = target.parent / f".{target.name}.tmp-{uuid.uuid4().hex}"
    shutil.copyfile(source, replacement)
    previous = target.with_name(f".{target.name}.previous-{uuid.uuid4().hex}")
    if target.exists():
        target.replace(previous)
    try:
        replacement.replace(target)
    except Exception:
        if previous.exists():
            previous.replace(target)
        raise
    if previous.exists():
        previous.unlink()
