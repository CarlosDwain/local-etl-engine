"""staging -> marts: business logic. TODO(step 3)."""

from etl.application.ports import LayerStore, QueryEngine
from etl.application.stages.base import RunContext, Stage
from etl.domain.results import StageResult


class MartStage(Stage[list[str]]):
    name = "marts"

    def __init__(self, engine: QueryEngine, store: LayerStore) -> None:
        self._engine = engine
        self._store = store

    def plan(self, ctx: RunContext) -> list[str]:
        raise NotImplementedError("TODO(step 3): order sql/marts by depends_on header")

    def execute(self, plan: list[str], ctx: RunContext) -> StageResult:
        raise NotImplementedError("TODO(step 3): run SQL for affected periods")
