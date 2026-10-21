"""marts -> Excel / Parquet outputs. TODO(step 3)."""

from collections.abc import Sequence

from etl.application.ports import Exporter
from etl.application.stages.base import RunContext, Stage
from etl.domain.results import StageResult


class ExportStage(Stage[list[str]]):
    name = "export"

    def __init__(self, exporters: Sequence[Exporter]) -> None:
        self._exporters = exporters

    def plan(self, ctx: RunContext) -> list[str]:
        raise NotImplementedError("TODO(step 3): list mart tables to export")

    def execute(self, plan: list[str], ctx: RunContext) -> StageResult:
        raise NotImplementedError("TODO(step 3): call each exporter, copy reports to output")
