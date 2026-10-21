"""Exporter writing Parquet. TODO(step 4)."""

from pathlib import Path


class ParquetExporter:
    def export(self, table: str, dest: Path) -> Path:
        raise NotImplementedError(
            "TODO(step 4): COPY table TO dest (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
