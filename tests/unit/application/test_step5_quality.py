from datetime import UTC, datetime
from pathlib import Path

import pytest

from etl.application.generated_key import generated_key, generated_keys
from etl.application.rejects import RejectThreshold
from etl.domain.errors import QualityGateError
from etl.infrastructure.archive.local_file_archiver import LocalFileArchiver


def test_generated_key_is_stable_and_occurrence_sensitive() -> None:
    row = {"account": "1000", "amount": "10.00"}

    assert generated_key(row, 0) == generated_key(row, 0)
    assert generated_key(row, 0) != generated_key(row, 1)


def test_generated_keys_increment_duplicate_material() -> None:
    row = {"account": "1000"}

    assert generated_keys((row, row))[0] != generated_keys((row, row))[1]


def test_reject_threshold_accepts_rate_at_limit() -> None:
    RejectThreshold(max_rate=0.10).enforce("GL.xlsx", 1, 10)


def test_reject_threshold_blocks_rate_above_limit() -> None:
    with pytest.raises(QualityGateError, match=r"GL\.xlsx"):
        RejectThreshold(max_rate=0.10).enforce("GL.xlsx", 2, 10)


def test_local_archiver_moves_file_into_period_and_timestamp(tmp_path: Path) -> None:
    source_dir = tmp_path / "landing"
    archive_root = tmp_path / "archive"
    source_dir.mkdir()
    source = source_dir / "GL_2026-01.xlsx"
    source.write_bytes(b"synthetic")

    archived = LocalFileArchiver(archive_root).archive(
        source, datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    )

    assert not source.exists()
    assert archived.is_file()
    assert archived.parent.parent.name == "2026-01"
