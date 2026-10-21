"""The runner: executes stages in order and reports progress. Knows nothing about the UI (A-11)."""

from collections.abc import Sequence
from typing import Any

from etl.application.ports import ProgressReporter, RunLogStore
from etl.application.stages.base import RunContext, RunOptions, Stage
from etl.domain.errors import EtlError
from etl.domain.results import RunSummary, StageResult


class PipelineRunner:
    def __init__(
        self,
        stages: Sequence[Stage[Any]],
        reporter: ProgressReporter,
        run_log: RunLogStore,
    ) -> None:
        self._stages = stages
        self._reporter = reporter
        self._run_log = run_log

    def run(self, options: RunOptions) -> RunSummary:
        ctx = RunContext(options=options, reporter=self._reporter)
        results: list[StageResult] = []
        total = len(self._stages)
        for index, stage in enumerate(self._stages):
            self._reporter.update(stage.name, index / total)
            try:
                result = stage.run(ctx)
            except EtlError as error:
                return RunSummary(tuple(results), error=f"{stage.name}: {error}")
            self._run_log.record_stage(result)
            results.append(result)
        self._reporter.update("done", 1.0)
        return RunSummary(tuple(results))
