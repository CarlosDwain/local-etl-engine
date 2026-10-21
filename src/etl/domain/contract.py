"""Data source contract: the rules for how one source enters the pipeline (D-9 to D-11)."""

from dataclasses import dataclass, field
from enum import StrEnum

from etl.domain.errors import ContractError


class DriftAction(StrEnum):
    FAIL = "fail"
    WARN = "warn"
    IGNORE = "ignore"


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
class DriftPolicy:
    missing_required_column: DriftAction = DriftAction.FAIL
    unknown_column: DriftAction = DriftAction.WARN


@dataclass(frozen=True)
class ColumnSpec:
    source: str  # header text in the Excel file
    name: str  # canonical snake_case name
    type: ColumnType
    required: bool = True
    aliases: tuple[str, ...] = ()
    precision: int | None = None
    scale: int | None = None

    def __post_init__(self) -> None:
        if self.type is ColumnType.DECIMAL:
            if (self.precision is None) != (self.scale is None):
                raise ContractError(
                    f"{self.name}: decimal precision and scale must be specified together"
                )
            if self.precision is not None and (
                self.precision < 1
                or self.scale is None
                or self.scale < 0
                or self.scale > self.precision
            ):
                raise ContractError(f"{self.name}: invalid decimal precision or scale")
        elif self.precision is not None or self.scale is not None:
            raise ContractError(
                f"{self.name}: precision and scale are only valid for decimal columns"
            )

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
    drift_policy: DriftPolicy = field(default_factory=DriftPolicy)
    max_reject_rate: float = 0.05

    def __post_init__(self) -> None:
        if not 0.0 <= self.max_reject_rate <= 1.0:
            raise ContractError(f"{self.name}: max_reject_rate must be between 0 and 1")
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
