"""Export a DuckDB table to XLSX with xlsxwriter."""

from pathlib import Path

import xlsxwriter

from etl.application.ports import QueryEngine


class XlsxExporter:
    def __init__(self, engine: QueryEngine) -> None:
        self._engine = engine

    def export(self, table: str, dest: Path) -> Path:
        columns = [str(row[1]) for row in self._engine.fetch_all(f"DESCRIBE {table}")]
        rows = self._engine.fetch_all(f"SELECT * FROM {table}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        workbook = xlsxwriter.Workbook(dest)
        worksheet = workbook.add_worksheet("Data")
        try:
            for column, name in enumerate(columns):
                worksheet.write(0, column, name)
            for row_index, row in enumerate(rows, start=1):
                for column, value in enumerate(row):
                    worksheet.write(row_index, column, value)
        finally:
            workbook.close()
        return dest
