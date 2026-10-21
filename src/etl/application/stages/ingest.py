"""Excel -> raw Parquet. TODO(step 3)."""

from etl.application.ports import (
    ContractRepository,
    FileSource,
    LayerStore,
    SourceReader,
)
from etl.application.stages.base import RunContext, Stage
from etl.domain.results import StageResult
from etl.domain.source_file import SourceFile


class IngestStage(Stage[list[SourceFile]]):
    name = "ingest"

    def __init__(
        self,
        contracts: ContractRepository,
        source: FileSource,
        reader: SourceReader,
        store: LayerStore,
    ) -> None:
        self._contracts = contracts
        self._source = source
        self._reader = reader
        self._store = store

    def plan(self, ctx: RunContext) -> list[SourceFile]:
        raise NotImplementedError("TODO(step 3): use ManifestService to skip unchanged files")

    def execute(self, plan: list[SourceFile], ctx: RunContext) -> StageResult:
        raise NotImplementedError("TODO(step 3): drift check, read as text, lineage, write raw")
