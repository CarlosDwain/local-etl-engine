"""Archive processed files in a dated local folder."""

import shutil
from datetime import UTC, datetime
from pathlib import Path


class LocalFileArchiver:
    def __init__(self, archive_root: Path) -> None:
        self._archive_root = archive_root

    def archive(self, source: Path, processed_at: datetime | None = None) -> Path:
        timestamp = processed_at or datetime.now(UTC)
        target_dir = (
            self._archive_root / timestamp.strftime("%Y-%m") / timestamp.strftime("%Y%m%d-%H%M%S")
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists():
            raise FileExistsError(f"Archive target already exists: {target}")
        return Path(shutil.move(str(source), str(target)))
