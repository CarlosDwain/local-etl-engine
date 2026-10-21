"""ManifestStore persisted in a small DuckDB file under <working>/state. TODO(step 3)."""

from etl.domain.manifest import ManifestEntry


class DuckDbManifestStore:
    def get(self, path: str) -> ManifestEntry | None:
        raise NotImplementedError("TODO(step 3)")

    def upsert(self, entry: ManifestEntry) -> None:
        raise NotImplementedError("TODO(step 3)")
