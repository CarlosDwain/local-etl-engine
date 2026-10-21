"""LayerStore for Parquet partitions. TODO(step 3)."""

from pathlib import Path

from etl.domain.layer import Layer
from etl.domain.period import Period


class ParquetLayerStore:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def write_partition(self, layer: Layer, table: str, period: Period, source: Path) -> None:
        raise NotImplementedError("TODO(step 3): atomic swap into <layer>/<table>/period=YYYY-MM")

    def list_partitions(self, layer: Layer, table: str) -> list[Period]:
        raise NotImplementedError("TODO(step 3): list period=* folders")
