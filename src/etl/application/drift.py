"""Compares a file's headers with its contract."""

from collections.abc import Iterable

from etl.domain.contract import Contract
from etl.domain.drift import DriftReport


class DriftDetector:
    def detect(self, contract: Contract, headers: Iterable[str]) -> DriftReport:
        found = {header.strip() for header in headers}
        missing = tuple(
            column.name
            for column in contract.required_columns
            if not found.intersection(column.accepted_headers)
        )
        declared = {header for column in contract.columns for header in column.accepted_headers}
        unknown = tuple(sorted(found - declared))
        return DriftReport(contract.name, missing_required=missing, unknown_headers=unknown)
