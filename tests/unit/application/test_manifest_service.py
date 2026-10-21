from datetime import UTC, datetime

from etl.application.manifest import ManifestService
from etl.domain.manifest import FileStatus, ManifestEntry
from tests.fakes import InMemoryManifestStore


def _entry(status: FileStatus = FileStatus.PROCESSED) -> ManifestEntry:
    return ManifestEntry("a.xlsx", "hash1", "contract1", status, datetime.now(UTC))


def test_unknown_file_needs_processing() -> None:
    service = ManifestService(InMemoryManifestStore())
    assert service.needs_processing("a.xlsx", "hash1", "contract1")


def test_unchanged_file_is_skipped() -> None:
    store = InMemoryManifestStore()
    store.upsert(_entry())
    assert not ManifestService(store).needs_processing("a.xlsx", "hash1", "contract1")


def test_changed_content_needs_processing() -> None:
    store = InMemoryManifestStore()
    store.upsert(_entry())
    assert ManifestService(store).needs_processing("a.xlsx", "hash2", "contract1")


def test_changed_contract_needs_processing() -> None:
    store = InMemoryManifestStore()
    store.upsert(_entry())
    assert ManifestService(store).needs_processing("a.xlsx", "hash1", "contract2")


def test_previously_failed_file_is_retried() -> None:
    store = InMemoryManifestStore()
    store.upsert(_entry(FileStatus.FAILED))
    assert ManifestService(store).needs_processing("a.xlsx", "hash1", "contract1")
