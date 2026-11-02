"""Read Excel worksheets into canonical text batches using python-calamine."""

from collections.abc import Iterator
from pathlib import Path

from python_calamine import CalamineWorkbook

from etl.application.ports import RawBatch
from etl.domain.contract import Contract

_BATCH_SIZE = 100_000


class CalamineExcelReader:
    def read(self, path: Path, contract: Contract) -> Iterator[RawBatch]:
        workbook = CalamineWorkbook.from_path(path)
        try:
            sheet = (
                workbook.get_sheet_by_name(contract.sheet.name)
                if contract.sheet.name is not None
                else workbook.get_sheet_by_index(0)
            )
            rows = sheet.to_python()
            header_index = contract.sheet.header_row - 1
            if header_index >= len(rows):
                return
            headers = [
                str(value).strip() if value is not None else "" for value in rows[header_index]
            ]
            header_map = _header_map(headers, contract)
            data_rows = rows[header_index + 1 :]
            if contract.sheet.skip_footer_rows:
                data_rows = data_rows[: -contract.sheet.skip_footer_rows]
            batch: list[dict[str, str | None]] = []
            for values in data_rows:
                if not any(value is not None for value in values):
                    continue
                row = {name: _text(values[index]) for name, index in header_map.items()}
                batch.append(row)
                if len(batch) == _BATCH_SIZE:
                    yield batch
                    batch = []
            if batch:
                yield batch
        finally:
            workbook.close()


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
    return str(value)
