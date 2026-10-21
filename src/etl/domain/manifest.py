"""Manifest record: which file version produced which data (D-13)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class FileStatus(StrEnum):
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    content_hash: str
    contract_hash: str
    status: FileStatus
    processed_at: datetime
