import pytest

from etl.infrastructure.engine.duckdb_engine import DuckDbEngine

pytestmark = pytest.mark.integration


def test_duckdb_engine_runs_parameterized_query() -> None:
    engine = DuckDbEngine()
    rows = engine.fetch_all("SELECT TRY_CAST($value AS INTEGER) AS n", {"value": "42"})
    assert rows == [(42,)]
    engine.close()


def test_duckdb_try_cast_returns_null_for_bad_value() -> None:
    engine = DuckDbEngine()
    rows = engine.fetch_all("SELECT TRY_CAST('12,5O0' AS DECIMAL(18, 2))")
    assert rows == [(None,)]
    engine.close()
