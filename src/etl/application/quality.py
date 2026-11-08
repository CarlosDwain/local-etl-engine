"""Data quality checks: small objects combined by a gate (A-9)."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
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


@dataclass(frozen=True)
class SqlQualityCheck:
    name: str
    sql_path: Path

    def run(self, engine: QueryEngine, table: str) -> CheckResult:
        del table
        sql = self.sql_path.read_text(encoding="utf-8").strip()
        rows = engine.fetch_all(sql)
        failures = int(str(rows[0][0])) if rows else 0
        return CheckResult(
            check=self.name,
            passed=failures == 0,
            detail=f"{failures} rows have null business keys" if failures else "",
        )


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
