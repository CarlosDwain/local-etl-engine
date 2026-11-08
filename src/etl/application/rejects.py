"""Evaluate row rejection thresholds."""

from dataclasses import dataclass

from etl.domain.errors import QualityGateError


@dataclass(frozen=True)
class RejectThreshold:
    max_rate: float = 0.05

    def __post_init__(self) -> None:
        if not 0.0 <= self.max_rate <= 1.0:
            raise ValueError("max_rate must be between 0 and 1")

    def enforce(self, source_file: str, rejected: int, total: int) -> None:
        if total == 0:
            return
        rate = rejected / total
        if rate > self.max_rate:
            raise QualityGateError(
                f"{source_file}: rejected {rejected} of {total} rows "
                f"({rate:.1%}), above limit {self.max_rate:.1%}"
            )
