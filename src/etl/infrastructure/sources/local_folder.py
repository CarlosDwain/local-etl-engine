"""FileSource for a local (or OneDrive-synced) folder."""

from datetime import UTC, datetime
from pathlib import Path

from etl.domain.source_file import SourceFile


class LocalFolderSource:
    """Lists files matching a glob. Files are already local, so ``fetch`` returns the path."""

    def __init__(self, root: Path, source: str, pattern: str) -> None:
        self._root = root
        self._source = source
        self._pattern = pattern

    def list_files(self) -> list[SourceFile]:
        files: list[SourceFile] = []
        for path in sorted(self._root.glob(self._pattern)):
            if not path.is_file():
                continue
            stat = path.stat()
            files.append(
                SourceFile(
                    source=self._source,
                    path=path,
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                )
            )
        return files

    def fetch(self, file: SourceFile, dest: Path) -> Path:
        return file.path
