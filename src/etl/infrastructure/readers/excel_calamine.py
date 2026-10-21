"""SourceReader for Excel using python-calamine. TODO(step 3)."""

from collections.abc import Iterator
from pathlib import Path

from etl.application.ports import RawBatch
from etl.domain.contract import Contract


class CalamineExcelReader:
    def read(self, path: Path, contract: Contract) -> Iterator[RawBatch]:
        raise NotImplementedError(
            "TODO(step 3): open sheet per contract.sheet, read all cells as text, yield batches"
        )
