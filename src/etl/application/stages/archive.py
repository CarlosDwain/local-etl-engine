"""Move completed source files to the archive."""

from pathlib import Path

from etl.application.ports import FileArchiver, FileSource
from etl.application.stages.base import RunContext, Stage
from etl.domain.results import StageResult


class ArchiveStage(Stage[list[Path]]):
    name = "archive"

    def __init__(self, source: FileSource, archiver: FileArchiver) -> None:
        self._source = source
        self._archiver = archiver

    def plan(self, ctx: RunContext) -> list[Path]:
        del ctx
        return [file.path for file in self._source.list_files() if file.path.is_file()]

    def execute(self, plan: list[Path], ctx: RunContext) -> StageResult:
        del ctx
        archived = [self._archiver.archive(path) for path in plan]
        return StageResult(stage=self.name, rows_out=len(archived))
