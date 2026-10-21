"""raw -> staging: TRY_CAST, dedupe, rejects. TODO(step 3)."""

from etl.application.ports import LayerStore, QueryEngine
from etl.application.stages.base import RunContext, Stage
from etl.domain.results import StageResult


class StagingStage(Stage[list[str]]):
    name = "staging"

    def __init__(self, engine: QueryEngine, store: LayerStore) -> None:
        self._engine = engine
        self._store = store

    def plan(self, ctx: RunContext) -> list[str]:
        raise NotImplementedError("TODO(step 3): list sql/staging files for changed partitions")

    def execute(self, plan: list[str], ctx: RunContext) -> StageResult:
        raise NotImplementedError("TODO(step 3): run SQL, route bad rows to rejects")
