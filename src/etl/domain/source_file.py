"""A file discovered in a source location."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    source: str  # contract name this file belongs to
    path: Path
    size_bytes: int
    modified_at: datetime
