from pathlib import Path

import pytest

from etl.application.stages.base import RunContext, RunOptions
from etl.application.stages.marts import MartStage
from etl.application.stages.staging import StagingStage
from etl.domain.layer import Layer
from etl.domain.period import Period
from etl.infrastructure.engine.duckdb_engine import DuckDbEngine
from etl.infrastructure.storage.parquet_store import ParquetLayerStore
from tests.fakes import RecordingReporter

pytestmark = pytest.mark.integration


def test_gl_vertical_slice_accumulates_all_periods(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    sql_dir = Path(__file__).parents[2] / "sql"
    engine = DuckDbEngine()
    store = ParquetLayerStore(data_dir)
    context = RunContext(RunOptions(), RecordingReporter())
    _write_raw_periods(engine, store)

    staging = StagingStage(engine, store, sql_dir, data_dir)
    staging_result = staging.run(context)
    marts = MartStage(engine, store, sql_dir)
    mart_result = marts.run(context)

    assert staging_result.rows_out == 3
    assert mart_result.rows_out == 3
    assert engine.fetch_all("SELECT count(*) FROM stg_gl_actuals") == [(3,)]
    assert engine.fetch_all("SELECT count(*) FROM mart_gl_actuals") == [(3,)]
    engine.close()


def _write_raw_periods(engine: DuckDbEngine, store: ParquetLayerStore) -> None:
    engine.execute(
        "CREATE TABLE _raw_period AS SELECT "
        "'INV-1' AS document_number, '1' AS line_number, '2025-01-01' AS posting_date, "
        "'1000' AS gl_account, '10.00' AS amount_usd, 'CC1' AS cost_center, "
        "'GL_2025-01.xlsx' AS _source_file, 'Sheet1' AS _sheet, "
        "3 AS _row_number, 'hash-1' AS _file_hash, '2025-01-01T00:00:00Z' AS _ingested_at"
    )
    store.export_relation(Layer.RAW, "gl_actuals", Period.parse("2025-01"), "_raw_period", engine)

    engine.execute(
        "INSERT INTO _raw_period VALUES "
        "('INV-2', '2', '2025-02-01', '1000', '20.00', 'CC1', "
        "'GL_2025-02.xlsx', 'Sheet1', 3, 'hash-2', '2025-02-01T00:00:00Z')"
    )
    engine.execute(
        "INSERT INTO _raw_period VALUES "
        "('INV-3', '3', '2025-02-01', '1000', '30.00', 'CC1', "
        "'GL_2025-02.xlsx', 'Sheet1', 4, 'hash-2', '2025-02-01T00:00:00Z')"
    )
    engine.execute(
        "CREATE TABLE _feb_raw AS SELECT * FROM _raw_period "
        "WHERE document_number IN ('INV-2', 'INV-3')"
    )
    store.export_relation(Layer.RAW, "gl_actuals", Period.parse("2025-02"), "_feb_raw", engine)
