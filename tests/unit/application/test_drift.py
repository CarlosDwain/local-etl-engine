from etl.application.drift import DriftDetector
from etl.domain.contract import ColumnSpec, ColumnType, Contract

CONTRACT = Contract(
    name="gl",
    version=1,
    file_pattern="*.xlsx",
    period_from_filename=r"(\d{4}-\d{2})",
    columns=(
        ColumnSpec("Amount (USD)", "amount_usd", ColumnType.DECIMAL, aliases=("Amt USD",)),
        ColumnSpec("GL Account", "gl_account", ColumnType.STRING),
        ColumnSpec("Cost Center", "cost_center", ColumnType.STRING, required=False),
    ),
    keys=("gl_account",),
)


def test_drift_clean_file_has_no_findings() -> None:
    report = DriftDetector().detect(CONTRACT, ["Amount (USD)", "GL Account", "Cost Center"])
    assert not report.is_blocking
    assert report.unknown_headers == ()


def test_drift_alias_counts_as_the_column() -> None:
    report = DriftDetector().detect(CONTRACT, ["Amt USD", "GL Account"])
    assert not report.is_blocking


def test_drift_missing_required_column_blocks() -> None:
    report = DriftDetector().detect(CONTRACT, ["GL Account"])
    assert report.is_blocking
    assert report.missing_required == ("amount_usd",)


def test_drift_unknown_header_is_reported_but_not_blocking() -> None:
    report = DriftDetector().detect(CONTRACT, ["Amount (USD)", "GL Account", "Region"])
    assert report.unknown_headers == ("Region",)
    assert not report.is_blocking
