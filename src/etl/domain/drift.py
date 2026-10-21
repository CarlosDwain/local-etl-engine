"""Schema drift: a file's structure no longer matches its contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DriftReport:
    source: str
    missing_required: tuple[str, ...] = ()  # canonical names of required columns not found
    unknown_headers: tuple[str, ...] = ()  # headers present but not declared

    @property
    def is_blocking(self) -> bool:
        """A missing required column fails the file (see data-standards drift policy)."""
        return bool(self.missing_required)
