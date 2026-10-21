"""Data quality checks: small objects combined by a gate (A-9)."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from etl.application.ports import QueryEngine
from etl.domain.errors import QualityGateError


@dataclass(frozen=True)
class CheckResult:
    check: str
    passed: bool
    detail: str = ""


class Check(Protocol):
    name: str

    def run(self, engine: QueryEngine, table: str) -> CheckResult: ...


class QualityGate:
    def __init__(self, checks: Sequence[Check]) -> None:
        self._checks = checks

    def evaluate(self, engine: QueryEngine, table: str) -> list[CheckResult]:
        return [check.run(engine, table) for check in self._checks]

    def enforce(self, engine: QueryEngine, table: str) -> None:
        failures = [result for result in self.evaluate(engine, table) if not result.passed]
        if failures:
            summary = "; ".join(f"{r.check}: {r.detail}" for r in failures)
            raise QualityGateError(f"{table} failed quality checks: {summary}")
