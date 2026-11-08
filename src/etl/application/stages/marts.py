"""Build mart tables from staging partitions."""

from pathlib import Path
from typing import cast

from etl.application.ports import LayerStore, QueryEngine
from etl.application.quality import Check, QualityGate, SqlQualityCheck
from etl.application.stages.base import RunContext, Stage
from etl.domain.layer import Layer
from etl.domain.period import Period
from etl.domain.results import StageResult


class MartStage(Stage[list[str]]):
    name = "marts"

    def __init__(self, engine: QueryEngine, store: LayerStore, sql_dir: Path) -> None:
        self._engine = engine
        self._store = store
        self._sql_dir = sql_dir

    def plan(self, ctx: RunContext) -> list[str]:
        del ctx
        plans: list[str] = []
        for sql_path in sorted((self._sql_dir / "marts").glob("*.sql")):
            for period in self._store.list_partitions(Layer.STAGING, "stg_gl_actuals"):
                plans.append(f"{sql_path.stem}:{period}")
        return plans

    def validate(self, result: StageResult, ctx: RunContext) -> None:
        del result, ctx
        quality_path = self._sql_dir / "quality" / "stg_gl_actuals.sql"
        if quality_path.is_file():
            check = cast(Check, SqlQualityCheck("business keys", quality_path))
            gate = QualityGate((check,))
            gate.enforce(self._engine, "stg_gl_actuals")

    def execute(self, plan: list[str], ctx: RunContext) -> StageResult:
        del ctx
        rows_out = 0
        table_names: set[str] = set()
        for item in plan:
            table, period_text = item.split(":", 1)
            period = Period.parse(period_text)
            if table not in table_names:
                table_names.add(table)
                output_table_exists = False
            else:
                output_table_exists = True
            select_sql = _sql_without_header(self._sql_dir / "marts" / f"{table}.sql")
            self._engine.execute(
                f"CREATE OR REPLACE TABLE _mart_period AS {select_sql} WHERE period = $period",
                {"period": period_text},
            )
            if output_table_exists:
                self._engine.execute(f"INSERT INTO {table} SELECT * FROM _mart_period")
            else:
                self._engine.execute(
                    f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _mart_period"
                )
            count = self._engine.fetch_all("SELECT count(*) FROM _mart_period")
            rows_out += int(str(count[0][0]))
            self._store.export_relation(Layer.MARTS, table, period, "_mart_period", self._engine)
        return StageResult(stage=self.name, rows_out=rows_out)


def _sql_without_header(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not line.startswith("--")).strip()
