"""Data source contract: the rules for how one source enters the pipeline (D-9 to D-11)."""

from dataclasses import dataclass, field
from enum import StrEnum

from etl.domain.errors import ContractError


class ColumnType(StrEnum):
    STRING = "string"
    DATE = "date"
    INT = "int"
    DECIMAL = "decimal"
    BOOL = "bool"


class ExtraColumns(StrEnum):
    DROP = "drop"
    WARN = "warn"
    KEEP = "keep"


@dataclass(frozen=True)
class ColumnSpec:
    source: str  # header text in the Excel file
    name: str  # canonical snake_case name
    type: ColumnType
    required: bool = True
    aliases: tuple[str, ...] = ()

    @property
    def accepted_headers(self) -> tuple[str, ...]:
        return (self.source, *self.aliases)


@dataclass(frozen=True)
class SheetSpec:
    name: str | None = None  # None means first sheet
    header_row: int = 1
    skip_footer_rows: int = 0


@dataclass(frozen=True)
class Contract:
    name: str
    version: int
    file_pattern: str
    period_from_filename: str  # regex with one group, YYYY-MM
    columns: tuple[ColumnSpec, ...]
    keys: tuple[str, ...] = ()
    generated_key: bool = False
    sheet: SheetSpec = field(default_factory=SheetSpec)
    extra_columns: ExtraColumns = ExtraColumns.WARN

    def __post_init__(self) -> None:
        names = [column.name for column in self.columns]
        if len(set(names)) != len(names):
            raise ContractError(f"{self.name}: duplicate column names")
        if not self.keys and not self.generated_key:
            raise ContractError(f"{self.name}: declare keys or set key_strategy: generated (D-10)")
        unknown = [key for key in self.keys if key not in names]
        if unknown:
            raise ContractError(f"{self.name}: keys not declared as columns: {unknown}")

    @property
    def required_columns(self) -> tuple[ColumnSpec, ...]:
        return tuple(column for column in self.columns if column.required)
