"""Ports: the sockets the application plugs tools into (A-5).

Each port is a small Protocol with one job. Adapters live in ``etl.infrastructure``.
Sketch only: refine signatures as the build steps need.
"""

from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Protocol

from etl.domain.contract import Contract
from etl.domain.layer import Layer
from etl.domain.manifest import ManifestEntry
from etl.domain.period import Period
from etl.domain.results import StageResult
from etl.domain.source_file import SourceFile

RawBatch = Sequence[Mapping[str, str | None]]  # rows as header -> text


class FileSource(Protocol):
    """Finds source files and makes them available locally (local folder, later Graph API)."""

    def list_files(self) -> list[SourceFile]: ...

    def fetch(self, file: SourceFile, dest: Path) -> Path: ...


class SourceReader(Protocol):
    """Reads one file into batches of text rows (Excel, later CSV)."""

    def read(self, path: Path, contract: Contract) -> Iterator[RawBatch]: ...


class QueryEngine(Protocol):
    """Runs SQL (DuckDB). Parameters are always passed separately (C-12)."""

    def execute(self, sql: str, params: Mapping[str, object] | None = None) -> None: ...

    def fetch_all(
        self, sql: str, params: Mapping[str, object] | None = None
    ) -> list[tuple[object, ...]]: ...


class LayerStore(Protocol):
    """Reads and atomically replaces Parquet partitions (D-8)."""

    def write_partition(self, layer: Layer, table: str, period: Period, source: Path) -> None: ...

    def list_partitions(self, layer: Layer, table: str) -> list[Period]: ...


class ManifestStore(Protocol):
    def get(self, path: str) -> ManifestEntry | None: ...

    def upsert(self, entry: ManifestEntry) -> None: ...


class RunLogStore(Protocol):
    def record_stage(self, result: StageResult) -> None: ...


class ContractRepository(Protocol):
    def load_all(self) -> list[Contract]: ...


class Exporter(Protocol):
    """Writes a finished table to an output file (Excel, Parquet)."""

    def export(self, table: str, dest: Path) -> Path: ...


class ProgressReporter(Protocol):
    """Receives progress between steps, never per row (A-11)."""

    def update(self, step: str, fraction: float) -> None: ...
