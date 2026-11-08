"""Build typed staging tables from raw Parquet partitions."""

from pathlib import Path

from etl.application.ports import ContractRepository, LayerStore, QueryEngine
from etl.application.rejects import RejectThreshold
from etl.application.stages.base import RunContext, Stage
from etl.domain.layer import Layer
from etl.domain.period import Period
from etl.domain.results import StageResult


class StagingStage(Stage[list[str]]):
    name = "staging"

    def __init__(
        self,
        engine: QueryEngine,
        store: LayerStore,
        sql_dir: Path,
        data_dir: Path,
        contracts: ContractRepository | None = None,
    ) -> None:
        self._engine = engine
        self._store = store
        self._sql_dir = sql_dir
        self._data_dir = data_dir
        self._contracts = contracts

    def plan(self, ctx: RunContext) -> list[str]:
        del ctx
        plans: list[str] = []
        for sql_path in sorted((self._sql_dir / "staging").glob("*.sql")):
            source = sql_path.stem.removeprefix("stg_")
            for period in self._store.list_partitions(Layer.RAW, source):
                plans.append(f"{sql_path.stem}:{period}")
        return plans

    def execute(self, plan: list[str], ctx: RunContext) -> StageResult:
        del ctx
        rows_out = 0
        rows_rejected = 0
        table_names: set[str] = set()
        raw_pattern = str(self._data_dir / "raw" / "gl_actuals" / "period=*" / "*.parquet")
        escaped_pattern = raw_pattern.replace("'", "''")
        self._engine.execute(
            "CREATE OR REPLACE VIEW raw_gl_actuals AS "
            f"SELECT * FROM read_parquet('{escaped_pattern}', hive_partitioning=true)"
        )
        for item in plan:
            table, period_text = item.split(":", 1)
            period = Period.parse(period_text)
            select_sql = _sql_without_header(self._sql_dir / "staging" / f"{table}.sql")
            self._engine.execute(
                f"CREATE OR REPLACE TABLE _staging_period AS {select_sql}",
                {"period": period_text},
            )
            if table in table_names:
                self._engine.execute(f"INSERT INTO {table} SELECT * FROM _staging_period")
            else:
                table_names.add(table)
                self._engine.execute(
                    f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _staging_period"
                )
            count = self._engine.fetch_all("SELECT count(*) FROM _staging_period")
            rows_out += int(str(count[0][0]))
            self._store.export_relation(
                Layer.STAGING, table, period, "_staging_period", self._engine
            )
            reject_sql_path = (
                self._sql_dir / "staging" / f"rejects_{table.removeprefix('stg_')}.sql"
            )
            if reject_sql_path.is_file():
                reject_sql = _sql_without_header(reject_sql_path)
                self._engine.execute(
                    f"CREATE OR REPLACE TABLE _rejects_period AS {reject_sql}",
                    {"period": period_text},
                )
                reject_count = self._engine.fetch_all("SELECT count(*) FROM _rejects_period")
                rows_rejected += int(str(reject_count[0][0]))
                if self._contracts is not None:
                    contract = next(
                        (
                            item
                            for item in self._contracts.load_all()
                            if table == f"stg_{item.name}"
                        ),
                        None,
                    )
                    if contract is not None:
                        totals = self._engine.fetch_all(
                            "SELECT _source_file, count(*) FROM raw_gl_actuals "
                            "WHERE period = $period GROUP BY _source_file",
                            {"period": period_text},
                        )
                        rejected_by_file = {
                            str(file): int(str(count))
                            for file, count in self._engine.fetch_all(
                                "SELECT _source_file, count(*) FROM _rejects_period "
                                "GROUP BY _source_file"
                            )
                        }
                        for source_file, total in totals:
                            RejectThreshold(contract.max_reject_rate).enforce(
                                str(source_file),
                                rejected_by_file.get(str(source_file), 0),
                                int(str(total)),
                            )
                if int(str(reject_count[0][0])) > 0:
                    self._store.export_relation(
                        Layer.STAGING,
                        f"_rejects/{table.removeprefix('stg_')}",
                        period,
                        "_rejects_period",
                        self._engine,
                    )
        return StageResult(stage=self.name, rows_out=rows_out, rows_rejected=rows_rejected)


def _sql_without_header(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not line.startswith("--")).strip()
