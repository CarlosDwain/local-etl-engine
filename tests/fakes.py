"""In-memory fakes for ports. Unit tests use these instead of real adapters (T-2)."""

from collections.abc import Mapping
from pathlib import Path

from etl.domain.manifest import ManifestEntry
from etl.domain.results import StageResult
from etl.domain.source_file import SourceFile


class FakeFileSource:
    def __init__(self, files: list[SourceFile] | None = None) -> None:
        self._files = files or []

    def list_files(self) -> list[SourceFile]:
        return list(self._files)

    def fetch(self, file: SourceFile, dest: Path) -> Path:
        return file.path


class InMemoryManifestStore:
    def __init__(self) -> None:
        self._entries: dict[str, ManifestEntry] = {}

    def get(self, path: str) -> ManifestEntry | None:
        return self._entries.get(path)

    def upsert(self, entry: ManifestEntry) -> None:
        self._entries[entry.path] = entry


class RecordingReporter:
    def __init__(self) -> None:
        self.events: list[tuple[str, float]] = []

    def update(self, step: str, fraction: float) -> None:
        self.events.append((step, fraction))


class InMemoryRunLog:
    def __init__(self) -> None:
        self.results: list[StageResult] = []

    def record_stage(self, result: StageResult) -> None:
        self.results.append(result)


class FakeEngine:
    """Records SQL instead of running it."""

    def __init__(self) -> None:
        self.executed: list[str] = []

    def execute(self, sql: str, params: Mapping[str, object] | None = None) -> None:
        self.executed.append(sql)

    def fetch_all(
        self, sql: str, params: Mapping[str, object] | None = None
    ) -> list[tuple[object, ...]]:
        self.executed.append(sql)
        return []
