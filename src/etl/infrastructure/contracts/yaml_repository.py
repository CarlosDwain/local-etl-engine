"""Load YAML source contracts and map validated boundary data into domain models."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    ValidationError,
    field_validator,
    model_validator,
)

from etl.domain.contract import (
    ColumnSpec,
    ColumnType,
    Contract,
    DriftAction,
    DriftPolicy,
    ExtraColumns,
    SheetSpec,
)
from etl.domain.errors import ContractError

_DECIMAL_PATTERN = re.compile(r"^decimal\((\d+),\s*(\d+)\)$")


class _YamlModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _ColumnDocument(_YamlModel):
    source: StrictStr
    name: StrictStr
    type: StrictStr
    required: StrictBool = True
    aliases: list[StrictStr] = Field(default_factory=list)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value in {"string", "date", "int", "bool"}:
            return value
        match = _DECIMAL_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("type must be string, date, int, bool, or decimal(precision,scale)")
        precision, scale = (int(part) for part in match.groups())
        if precision < 1 or scale > precision:
            raise ValueError("decimal precision must be positive and scale cannot exceed precision")
        return value


class _SheetDocument(_YamlModel):
    name: StrictStr | None = None
    header_row: int = Field(default=1, strict=True, ge=1)
    skip_footer_rows: int = Field(default=0, strict=True, ge=0)


class _DriftPolicyDocument(_YamlModel):
    missing_required_column: DriftAction = DriftAction.FAIL
    unknown_column: DriftAction = DriftAction.WARN


class _PartialDriftPolicyDocument(_YamlModel):
    missing_required_column: DriftAction | None = None
    unknown_column: DriftAction | None = None


class _DefaultsDocument(_YamlModel):
    extra_columns: ExtraColumns | None = None
    on_drift: _PartialDriftPolicyDocument | None = None
    max_reject_rate: float | None = Field(default=None, strict=True, ge=0.0, le=1.0)


class _ContractDocument(_YamlModel):
    name: StrictStr
    version: int = Field(strict=True, ge=1)
    file_pattern: StrictStr
    period_from_filename: StrictStr
    sheet: _SheetDocument = Field(default_factory=_SheetDocument)
    columns: list[_ColumnDocument] = Field(min_length=1)
    keys: list[StrictStr] = Field(default_factory=list)
    key_strategy: Literal["generated"] | None = None
    extra_columns: ExtraColumns = ExtraColumns.WARN
    on_drift: _DriftPolicyDocument = Field(default_factory=_DriftPolicyDocument)
    max_reject_rate: float = Field(default=0.05, strict=True, ge=0.0, le=1.0)

    @field_validator("period_from_filename")
    @classmethod
    def validate_period_pattern(cls, value: str) -> str:
        try:
            pattern = re.compile(value)
        except re.error as error:
            raise ValueError(f"must be a valid regular expression: {error}") from error
        if pattern.groups != 1:
            raise ValueError("must contain exactly one capture group for the reporting period")
        return value

    @model_validator(mode="after")
    def validate_key_strategy(self) -> _ContractDocument:
        if self.key_strategy == "generated" and self.keys:
            raise ValueError("declare keys or key_strategy: generated, not both")
        return self


class YamlContractRepository:
    def __init__(self, contracts_dir: Path) -> None:
        self._contracts_dir = contracts_dir

    def load_all(self) -> list[Contract]:
        if not self._contracts_dir.is_dir():
            raise ContractError(f"Contracts directory not found: {self._contracts_dir}")

        defaults_path = self._contracts_dir / "_defaults.yaml"
        defaults = self._load_defaults(defaults_path) if defaults_path.exists() else {}
        contracts: list[Contract] = []
        for path in sorted(self._contracts_dir.glob("*.yaml")):
            if path.name == "_defaults.yaml" or not path.is_file():
                continue
            merged = self._merge_defaults(defaults, self._read_yaml(path))
            try:
                document = _ContractDocument.model_validate(merged)
            except ValidationError as error:
                raise self._validation_error(path, "invalid contract", error) from error
            contracts.append(self._to_domain(document, path))
        return contracts

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, object]:
        try:
            contents = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            raise ContractError(f"Could not read {path.name}: {error}") from error

        if contents is None:
            return {}
        if not isinstance(contents, Mapping):
            raise ContractError(f"{path.name}: YAML document must be a mapping")
        if any(not isinstance(key, str) for key in contents):
            raise ContractError(f"{path.name}: YAML mapping keys must be strings")
        return dict(contents)

    def _load_defaults(self, path: Path) -> dict[str, object]:
        raw_defaults = self._read_yaml(path)
        try:
            defaults = _DefaultsDocument.model_validate(raw_defaults)
        except ValidationError as error:
            raise self._validation_error(path, "invalid defaults", error) from error
        return defaults.model_dump(exclude_unset=True)

    @staticmethod
    def _merge_defaults(
        defaults: dict[str, object], contract: dict[str, object]
    ) -> dict[str, object]:
        merged = defaults.copy()
        default_drift = defaults.get("on_drift")
        contract_drift = contract.get("on_drift")
        if isinstance(default_drift, Mapping) and isinstance(contract_drift, Mapping):
            merged["on_drift"] = {**default_drift, **contract_drift}
        merged.update(
            {
                key: value
                for key, value in contract.items()
                if key != "on_drift" or not isinstance(contract_drift, Mapping)
            }
        )
        return merged

    @staticmethod
    def _validation_error(path: Path, label: str, error: ValidationError) -> ContractError:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        return ContractError(f"{path.name}: {label}: {details}")

    @staticmethod
    def _to_domain(document: _ContractDocument, path: Path) -> Contract:
        columns: list[ColumnSpec] = []
        for column in document.columns:
            decimal = _DECIMAL_PATTERN.fullmatch(column.type)
            columns.append(
                ColumnSpec(
                    source=column.source,
                    name=column.name,
                    type=ColumnType.DECIMAL if decimal else ColumnType(column.type),
                    required=column.required,
                    aliases=tuple(column.aliases),
                    precision=int(decimal.group(1)) if decimal else None,
                    scale=int(decimal.group(2)) if decimal else None,
                )
            )

        try:
            return Contract(
                name=document.name,
                version=document.version,
                file_pattern=document.file_pattern,
                period_from_filename=document.period_from_filename,
                columns=tuple(columns),
                keys=tuple(document.keys),
                generated_key=document.key_strategy == "generated",
                sheet=SheetSpec(
                    name=document.sheet.name,
                    header_row=document.sheet.header_row,
                    skip_footer_rows=document.sheet.skip_footer_rows,
                ),
                extra_columns=document.extra_columns,
                drift_policy=DriftPolicy(
                    missing_required_column=document.on_drift.missing_required_column,
                    unknown_column=document.on_drift.unknown_column,
                ),
                max_reject_rate=document.max_reject_rate,
            )
        except ContractError as error:
            raise ContractError(f"{path.name}: {error}") from error
