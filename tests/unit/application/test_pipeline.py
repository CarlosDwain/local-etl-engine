from etl.application.pipeline import PipelineRunner
from etl.application.stages.base import RunContext, RunOptions, Stage
from etl.domain.errors import IngestError
from etl.domain.results import StageResult
from tests.fakes import InMemoryRunLog, RecordingReporter


class OkStage(Stage[int]):
    name = "ok"

    def plan(self, ctx: RunContext) -> int:
        return 3

    def execute(self, plan: int, ctx: RunContext) -> StageResult:
        return StageResult(self.name, rows_in=plan, rows_out=plan)


class BoomStage(Stage[int]):
    name = "boom"

    def plan(self, ctx: RunContext) -> int:
        return 0

    def execute(self, plan: int, ctx: RunContext) -> StageResult:
        raise IngestError("file unreadable")


def test_runner_runs_stages_in_order_and_logs_each() -> None:
    log = InMemoryRunLog()
    reporter = RecordingReporter()
    summary = PipelineRunner([OkStage(), OkStage()], reporter, log).run(RunOptions())
    assert summary.ok
    assert len(summary.results) == 2
    assert len(log.results) == 2
    assert reporter.events[-1] == ("done", 1.0)


def test_runner_stops_and_reports_on_etl_error() -> None:
    log = InMemoryRunLog()
    summary = PipelineRunner([OkStage(), BoomStage(), OkStage()], RecordingReporter(), log).run(
        RunOptions()
    )
    assert not summary.ok
    assert summary.error == "boom: file unreadable"
    assert len(summary.results) == 1


def test_runner_with_no_stages_succeeds() -> None:
    summary = PipelineRunner([], RecordingReporter(), InMemoryRunLog()).run(RunOptions())
    assert summary.ok
