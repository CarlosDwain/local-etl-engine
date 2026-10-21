"""Exporter writing Excel with xlsxwriter. TODO(step 3)."""

from pathlib import Path


class XlsxExporter:
    def export(self, table: str, dest: Path) -> Path:
        raise NotImplementedError("TODO(step 3): stream table rows to .xlsx")
