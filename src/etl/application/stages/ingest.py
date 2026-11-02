"""Excel files to partitioned raw Parquet."""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from etl.application.manifest import ManifestService
from etl.application.ports import (
    ContractRepository,
    FileSource,
    LayerStore,
    ManifestStore,
    SourceReader,
)
from etl.application.stages.base import RunContext, Stage
from etl.domain.contract import Contract
from etl.domain.errors import IngestError
from etl.domain.layer import Layer
from etl.domain.manifest import FileStatus, ManifestEntry
from etl.domain.period import Period
from etl.domain.results import StageResult
from etl.domain.source_file import SourceFile


class IngestStage(Stage[list[SourceFile]]):
    name = "ingest"

    def __init__(
        self,
        contracts: ContractRepository,
        source: FileSource,
        reader: SourceReader,
        store: LayerStore,
        manifest_store: ManifestStore,
    ) -> None:
        self._contracts = contracts
        self._source = source
        self._reader = reader
        self._store = store
        self._manifest_store = manifest_store
        self._manifest = ManifestService(manifest_store)

    def plan(self, ctx: RunContext) -> list[SourceFile]:
        del ctx
        planned: list[SourceFile] = []
        for contract in self._contracts.load_all():
            if contract.name not in {file.source for file in self._source.list_files()}:
                continue
            contract_hash = _contract_hash(contract)
            for file in self._source.list_files():
                if file.source != contract.name:
                    continue
                if self._manifest.needs_processing(
                    str(file.path), _sha256(file.path), contract_hash
                ):
                    planned.append(file)
        return planned

    def execute(self, plan: list[SourceFile], ctx: RunContext) -> StageResult:
        del ctx
        contracts = {contract.name: contract for contract in self._contracts.load_all()}
        rows_out = 0
        for file in plan:
            contract = contracts[file.source]
            period_match = re.fullmatch(contract.period_from_filename, file.path.name)
            if period_match is None:
                raise IngestError(f"Could not determine period from {file.path.name}")
            period = Period.parse(period_match.group(1))
            file_hash = _sha256(file.path)
            ingested_at = datetime.now(UTC).isoformat()
            columns = [column.name for column in contract.columns]
            columns += [
                "_source_file",
                "_sheet",
                "_row_number",
                "_file_hash",
                "_ingested_at",
                "period",
            ]
            raw_rows: list[list[str | None]] = []
            row_number = contract.sheet.header_row + 1
            for batch in self._reader.read(file.path, contract):
                for row in batch:
                    raw_row = [row.get(column.name) for column in contract.columns]
                    raw_row += [
                        file.path.name,
                        contract.sheet.name or "Sheet1",
                        str(row_number),
                        file_hash,
                        ingested_at,
                        str(period),
                    ]
                    raw_rows.append(raw_row)
                    row_number += 1
            self._store.write_rows(Layer.RAW, contract.name, period, columns, raw_rows)
            rows_out += len(raw_rows)
            self._manifest_store.upsert(
                ManifestEntry(
                    path=str(file.path),
                    content_hash=file_hash,
                    contract_hash=_contract_hash(contract),
                    status=FileStatus.PROCESSED,
                    processed_at=datetime.now(UTC),
                )
            )
        return StageResult(stage=self.name, rows_in=len(plan), rows_out=rows_out)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _contract_hash(contract: Contract) -> str:
    value = {
        "name": contract.name,
        "version": contract.version,
        "sheet": contract.sheet.__dict__,
        "columns": [column.__dict__ for column in contract.columns],
        "keys": contract.keys,
    }
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
