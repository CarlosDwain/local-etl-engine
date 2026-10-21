"""Decides whether a file needs processing (incremental logic, D-13)."""

from etl.application.ports import ManifestStore
from etl.domain.manifest import FileStatus


class ManifestService:
    """The only place that answers "has this file changed?" so storage details stay hidden."""

    def __init__(self, store: ManifestStore) -> None:
        self._store = store

    def needs_processing(self, path: str, content_hash: str, contract_hash: str) -> bool:
        entry = self._store.get(path)
        if entry is None:
            return True
        return (
            entry.status is FileStatus.FAILED
            or entry.content_hash != content_hash
            or entry.contract_hash != contract_hash
        )
