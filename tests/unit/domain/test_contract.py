import pytest

from etl.domain.contract import ColumnSpec, ColumnType, Contract
from etl.domain.errors import ContractError


def _column(name: str, *, required: bool = True) -> ColumnSpec:
    return ColumnSpec(source=name.title(), name=name, type=ColumnType.STRING, required=required)


def _contract(**overrides: object) -> Contract:
    fields: dict[str, object] = {
        "name": "demo",
        "version": 1,
        "file_pattern": "*.xlsx",
        "period_from_filename": r"(\d{4}-\d{2})",
        "columns": (_column("a"), _column("b", required=False)),
        "keys": ("a",),
    }
    fields.update(overrides)
    return Contract(**fields)  # type: ignore[arg-type]


def test_contract_exposes_required_columns() -> None:
    assert [c.name for c in _contract().required_columns] == ["a"]


def test_contract_requires_a_key_or_generated_key() -> None:
    with pytest.raises(ContractError):
        _contract(keys=())


def test_contract_allows_generated_key_without_keys() -> None:
    assert _contract(keys=(), generated_key=True).generated_key


def test_contract_rejects_keys_that_are_not_columns() -> None:
    with pytest.raises(ContractError):
        _contract(keys=("missing",))


def test_contract_rejects_duplicate_column_names() -> None:
    with pytest.raises(ContractError):
        _contract(columns=(_column("a"), _column("a")))
