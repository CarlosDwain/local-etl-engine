"""Composition root (A-4): the only place that constructs concrete adapters.

Use explicit imports, never dynamic discovery (C-10): PyInstaller cannot see dynamic imports.
"""

from etl.application.pipeline import PipelineRunner
from etl.config import AppConfig
from etl.infrastructure.state.logging_run_log import LoggingRunLogStore
from etl.interfaces.cli.console_reporter import ConsoleReporter


def build_runner(config: AppConfig) -> PipelineRunner:
    """Wire the pipeline. Stages are added here as build steps complete.

    TODO(step 3): construct YamlContractRepository, LocalFolderSource, CalamineExcelReader,
    DuckDbEngine, ParquetLayerStore, DuckDbManifestStore, then Ingest/Staging/Mart/Export stages.
    """
    return PipelineRunner(stages=[], reporter=ConsoleReporter(), run_log=LoggingRunLogStore())
