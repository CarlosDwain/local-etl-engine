from pathlib import Path

import pytest

from etl.domain.contract import ColumnSpec, ColumnType, Contract, SheetSpec
from etl.domain.errors import IngestError
from etl.infrastructure.engine.duckdb_engine import DuckDbEngine
from etl.infrastructure.exporters.parquet_exporter import ParquetExporter
from etl.infrastructure.readers.csv_reader import CsvReader
from etl.infrastructure.sources.graph_api import GraphApiSource

pytestmark = pytest.mark.integration


def _contract() -> Contract:
    return Contract(
        name="demo",
        version=1,
        file_pattern="*.csv",
        period_from_filename=r"demo_(\d{4}-\d{2})\.csv",
        sheet=SheetSpec(header_row=1),
        columns=(
            ColumnSpec(source="Document Number", name="document_number", type=ColumnType.STRING),
            ColumnSpec(source="Amount", name="amount", type=ColumnType.STRING),
        ),
        keys=("document_number",),
    )


def test_csv_reader_maps_headers_and_returns_text(tmp_path: Path) -> None:
    source = tmp_path / "demo_2026-01.csv"
    source.write_text(
        "Document Number,Amount\nINV-1,12.50\nINV-2,\n",
        encoding="utf-8",
    )

    batches = list(CsvReader().read(source, _contract()))

    assert batches == [
        [
            {"document_number": "INV-1", "amount": "12.50"},
            {"document_number": "INV-2", "amount": None},
        ]
    ]


def test_parquet_exporter_writes_compressed_parquet(tmp_path: Path) -> None:
    engine = DuckDbEngine()
    engine.execute("CREATE TABLE result AS SELECT 42 AS value")
    destination = tmp_path / "result.parquet"

    exported = ParquetExporter(engine).export("result", destination)

    assert exported == destination
    assert destination.is_file()
    engine.execute(
        "CREATE TABLE imported AS SELECT * FROM read_parquet($path)", {"path": str(destination)}
    )
    assert engine.fetch_all("SELECT value FROM imported") == [(42,)]
    engine.close()


def test_graph_api_source_is_an_explicit_stub() -> None:
    with pytest.raises(IngestError, match="not implemented"):
        GraphApiSource().list_files()
