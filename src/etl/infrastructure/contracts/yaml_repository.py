"""ContractRepository reading ``contracts/*.yaml``. TODO(step 1).

Plan: parse each YAML with a Pydantic schema (merging ``_defaults.yaml``), then map into the frozen
domain ``Contract``. Pydantic stays in this file (C-4). Malformed contracts raise ``ContractError``.
"""

from pathlib import Path

from etl.domain.contract import Contract


class YamlContractRepository:
    def __init__(self, contracts_dir: Path) -> None:
        self._contracts_dir = contracts_dir

    def load_all(self) -> list[Contract]:
        raise NotImplementedError("TODO(step 1): Pydantic schema + _defaults.yaml merge")
