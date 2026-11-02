"""Placeholder Microsoft Graph file source for a later implementation."""

from pathlib import Path

from etl.domain.errors import IngestError
from etl.domain.source_file import SourceFile


class GraphApiSource:
    def list_files(self) -> list[SourceFile]:
        raise IngestError(
            "Microsoft Graph source is not implemented yet; configure a local folder source"
        )

    def fetch(self, file: SourceFile, dest: Path) -> Path:
        del file, dest
        raise IngestError(
            "Microsoft Graph source is not implemented yet; configure a local folder source"
        )
