"""A source row that could not pass staging validation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RejectRow:
    source_file: str
    row_number: int
    column: str
    value: str | None
    reason: str


@dataclass(frozen=True)
class RejectReport:
    rows: tuple[RejectRow, ...] = ()

    @property
    def count(self) -> int:
        return len(self.rows)
