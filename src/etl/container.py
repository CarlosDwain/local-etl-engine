"""Composition root (A-4): the only place that constructs concrete adapters.

Use explicit imports, never dynamic discovery (C-10): PyInstaller cannot see dynamic imports.
"""

from etl.application.pipeline import PipelineRunner
from etl.application.stages.export import ExportStage
from etl.application.stages.ingest import IngestStage
from etl.application.stages.marts import MartStage
from etl.application.stages.staging import StagingStage
from etl.config import AppConfig
from etl.infrastructure.contracts.yaml_repository import YamlContractRepository
from etl.infrastructure.engine.duckdb_engine import DuckDbEngine
from etl.infrastructure.exporters.excel_xlsxwriter import XlsxExporter
from etl.infrastructure.readers.excel_calamine import CalamineExcelReader
from etl.infrastructure.sources.local_folder import LocalFolderSource
from etl.infrastructure.state.duckdb_manifest_store import DuckDbManifestStore
from etl.infrastructure.state.logging_run_log import LoggingRunLogStore
from etl.infrastructure.storage.parquet_store import ParquetLayerStore
from etl.interfaces.cli.console_reporter import ConsoleReporter


def build_runner(config: AppConfig) -> PipelineRunner:
    """Compose the Step 3 vertical slice for the configured GL source."""
    contracts = YamlContractRepository(config.contracts_dir)
    gl_contract = next(
        contract for contract in contracts.load_all() if contract.name == "gl_actuals"
    )
    data_dir = config.working_dir / "data"
    sql_dir = config.contracts_dir.parent / "sql"
    engine = DuckDbEngine(str(config.working_dir / "state" / "etl.duckdb"))
    store = ParquetLayerStore(data_dir)
    manifest = DuckDbManifestStore(config.working_dir / "state" / "manifest.duckdb")
    source = LocalFolderSource(config.source_dir, gl_contract.name, gl_contract.file_pattern)
    reader = CalamineExcelReader()
    exporter = XlsxExporter(engine)
    stages = (
        IngestStage(contracts, source, reader, store, manifest),
        StagingStage(engine, store, sql_dir, data_dir),
        MartStage(engine, store, sql_dir),
        ExportStage((exporter,), store, config.output_dir),
    )
    return PipelineRunner(stages=stages, reporter=ConsoleReporter(), run_log=LoggingRunLogStore())
