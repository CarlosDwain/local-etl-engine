"""Result objects returned by stages and the runner (E-1)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RejectRow:
    source: str
    file: str
    row_number: int
    column: str
    value: str | None
    reason: str


@dataclass(frozen=True)
class StageResult:
    stage: str
    rows_in: int = 0
    rows_out: int = 0
    rows_rejected: int = 0
    files_failed: int = 0
    messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunSummary:
    results: tuple[StageResult, ...] = ()
    error: str | None = None  # set when the run stopped on an EtlError

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def rows_rejected(self) -> int:
        return sum(result.rows_rejected for result in self.results)

    @property
    def files_failed(self) -> int:
        return sum(result.files_failed for result in self.results)
