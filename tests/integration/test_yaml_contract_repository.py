from pathlib import Path

import pytest

from etl.domain.contract import DriftAction, ExtraColumns
from etl.domain.errors import ContractError
from etl.infrastructure.contracts.yaml_repository import YamlContractRepository

pytestmark = pytest.mark.integration

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"


def test_yaml_contract_repository_loads_example_contract() -> None:
    contracts = YamlContractRepository(CONTRACTS_DIR).load_all()

    assert len(contracts) == 1
    contract = contracts[0]
    assert contract.name == "gl_actuals"
    assert contract.keys == ("document_number", "line_number")
    assert contract.extra_columns is ExtraColumns.WARN
    assert contract.max_reject_rate == 0.05
    assert contract.drift_policy.missing_required_column is DriftAction.FAIL
    assert contract.drift_policy.unknown_column is DriftAction.WARN
    amount = next(column for column in contract.columns if column.name == "amount_usd")
    assert amount.precision == 18
    assert amount.scale == 2


def test_yaml_contract_repository_merges_defaults_with_contract_overrides(
    tmp_path: Path,
) -> None:
    (tmp_path / "_defaults.yaml").write_text(
        "extra_columns: warn\n"
        "on_drift:\n"
        "  missing_required_column: fail\n"
        "  unknown_column: warn\n"
        "max_reject_rate: 0.05\n",
        encoding="utf-8",
    )
    (tmp_path / "demo.yaml").write_text(
        "name: demo\n"
        "version: 1\n"
        "file_pattern: '*.xlsx'\n"
        "period_from_filename: '(\\\\d{4}-\\\\d{2})'\n"
        "columns:\n"
        "  - {source: Account, name: account, type: string}\n"
        "keys: [account]\n"
        "extra_columns: keep\n"
        "on_drift:\n"
        "  unknown_column: ignore\n"
        "max_reject_rate: 0.1\n",
        encoding="utf-8",
    )

    contract = YamlContractRepository(tmp_path).load_all()[0]

    assert contract.extra_columns is ExtraColumns.KEEP
    assert contract.drift_policy.missing_required_column is DriftAction.FAIL
    assert contract.drift_policy.unknown_column is DriftAction.IGNORE
    assert contract.max_reject_rate == 0.1


def test_yaml_contract_repository_reports_malformed_contract(
    tmp_path: Path,
) -> None:
    (tmp_path / "broken.yaml").write_text(
        "name: broken\nversion: invalid\ncolumns: []\n",
        encoding="utf-8",
    )

    with pytest.raises(ContractError, match=r"broken\.yaml: invalid contract"):
        YamlContractRepository(tmp_path).load_all()
