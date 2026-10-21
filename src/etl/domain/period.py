"""Reporting period (a calendar month). Partition key for every layer."""

import re
from dataclasses import dataclass
from typing import Self

_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")


@dataclass(frozen=True, order=True)
class Period:
    year: int
    month: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"month must be 1-12, got {self.month}")
        if not 1900 <= self.year <= 2999:
            raise ValueError(f"year out of range: {self.year}")

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse ``YYYY-MM``. Raises ``ValueError`` on anything else."""
        match = _PATTERN.match(text.strip())
        if match is None:
            raise ValueError(f"expected YYYY-MM, got {text!r}")
        return cls(int(match.group(1)), int(match.group(2)))

    @property
    def partition_dir(self) -> str:
        """Hive-style folder name, for example ``period=2026-09``."""
        return f"period={self}"

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"
