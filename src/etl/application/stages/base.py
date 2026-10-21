"""Stage template method (A-8): plan -> execute -> validate -> commit."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from etl.application.ports import ProgressReporter
from etl.domain.period import Period
from etl.domain.results import StageResult


@dataclass(frozen=True)
class RunOptions:
    full_refresh: bool = False
    sources: tuple[str, ...] = ()  # empty means all sources
    period_from: Period | None = None
    period_to: Period | None = None


@dataclass(frozen=True)
class RunContext:
    options: RunOptions
    reporter: ProgressReporter


class Stage[PlanT](ABC):
    """Subclasses implement ``plan`` and ``execute``. Do not override ``run``."""

    name: ClassVar[str]

    def run(self, ctx: RunContext) -> StageResult:
        plan = self.plan(ctx)
        result = self.execute(plan, ctx)
        self.validate(result, ctx)
        self.commit(result, ctx)
        return result

    @abstractmethod
    def plan(self, ctx: RunContext) -> PlanT:
        """Decide what needs doing (incremental logic lives here)."""

    @abstractmethod
    def execute(self, plan: PlanT, ctx: RunContext) -> StageResult:
        """Do the work described by the plan."""

    def validate(self, result: StageResult, ctx: RunContext) -> None:  # noqa: B027
        """Optional hook: run quality gates. Raise ``QualityGateError`` to stop the run."""

    def commit(self, result: StageResult, ctx: RunContext) -> None:  # noqa: B027
        """Optional hook: atomically publish outputs and update the manifest."""
