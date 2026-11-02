"""Read CSV files into canonical text batches."""

import csv
from collections import deque
from collections.abc import Iterator
from pathlib import Path

from etl.application.ports import RawBatch
from etl.domain.contract import Contract

_BATCH_SIZE = 100_000


class CsvReader:
    def read(self, path: Path, contract: Contract) -> Iterator[RawBatch]:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            for _ in range(contract.sheet.header_row - 1):
                if source.readline() == "":
                    return
            reader = csv.DictReader(source)
            if reader.fieldnames is None:
                return
            fieldnames = list(reader.fieldnames)
            headers = [header.strip() for header in fieldnames]
            header_map = _header_map(headers, contract)
            pending: deque[dict[str, str | None]] = deque(
                maxlen=contract.sheet.skip_footer_rows + 1
            )
            batch: list[dict[str, str | None]] = []
            for csv_row in reader:
                if contract.sheet.skip_footer_rows:
                    pending.append(csv_row)
                    if len(pending) > contract.sheet.skip_footer_rows:
                        csv_row = pending.popleft()
                    else:
                        continue
                if not any(value not in (None, "") for value in csv_row.values()):
                    continue
                row = {
                    name: _text(csv_row.get(fieldnames[index]))
                    for name, index in header_map.items()
                }
                batch.append(row)
                if len(batch) == _BATCH_SIZE:
                    yield batch
                    batch = []
            if batch:
                yield batch


def _header_map(headers: list[str], contract: Contract) -> dict[str, int]:
    result: dict[str, int] = {}
    for column in contract.columns:
        for index, header in enumerate(headers):
            if header in column.accepted_headers:
                result[column.name] = index
                break
    return result


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text != "" else None
