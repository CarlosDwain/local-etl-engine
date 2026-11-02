"""Export completed marts to configured output formats."""

from collections.abc import Sequence
from pathlib import Path

from etl.application.ports import Exporter, LayerStore
from etl.application.stages.base import RunContext, Stage
from etl.domain.layer import Layer
from etl.domain.results import StageResult


class ExportStage(Stage[list[str]]):
    name = "export"

    def __init__(self, exporters: Sequence[Exporter], store: LayerStore, output_dir: Path) -> None:
        self._exporters = exporters
        self._store = store
        self._output_dir = output_dir

    def plan(self, ctx: RunContext) -> list[str]:
        del ctx
        return sorted(
            table
            for table in {"mart_gl_actuals"}
            if self._store.list_partitions(Layer.MARTS, table)
        )

    def execute(self, plan: list[str], ctx: RunContext) -> StageResult:
        del ctx
        self._output_dir.mkdir(parents=True, exist_ok=True)
        for table in plan:
            for exporter in self._exporters:
                exporter.export(table, self._output_dir / f"{table}.xlsx")
        return StageResult(stage=self.name, rows_out=len(plan))
