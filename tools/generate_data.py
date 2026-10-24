# pyright: reportMissingTypeStubs=false
"""Generate deterministic synthetic Excel sources for pipeline development and tests."""

import argparse
import json
import logging
import random
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Protocol, cast

import xlsxwriter

LOGGER = logging.getLogger("etl.synthetic_data")
BENCHMARK_SIZES = (100_000, 1_000_000, 5_000_000)
DATASET_PROFILES = ("messy", "clean")
MAX_BENCHMARK_ROWS = BENCHMARK_SIZES[-1]
EXCEL_MAX_ROWS = 1_048_576
TITLE_ROWS = 2
HEADER_ROW = 3
FOOTER_ROWS = 1
MAX_DATA_ROWS_PER_SHEET = EXCEL_MAX_ROWS - TITLE_ROWS - 1 - FOOTER_ROWS
ISSUE_CYCLE_ROWS = 10_000
PERIODS = (
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
)
ISSUE_SPECS: dict[int, tuple[str, str, str]] = {
    100: ("malformed_amount", "amount_usd", "not-a-number"),
    200: ("accounting_negative", "amount_usd", "(500)"),
    300: ("thousands_separator", "amount_usd", "1,234.56"),
    400: ("null_required", "document_number", ""),
    500: ("duplicate_row", "_business_key", ""),
}


class _WorksheetWriter(Protocol):
    def write(self, row: int, column: int, value: object) -> object: ...

    def write_row(self, row: int, column: int, data: Sequence[object]) -> object: ...


class _WorkbookWriter(Protocol):
    def add_worksheet(self, name: str | None = None) -> _WorksheetWriter: ...

    def close(self) -> None: ...


def generate_dataset(
    output_dir: Path,
    row_count: int,
    seed: int,
    profile: Literal["messy", "clean"] = "messy",
) -> Path:
    """Write source workbooks and ground truth without overwriting existing files."""
    if not 1 <= row_count <= MAX_BENCHMARK_ROWS:
        raise ValueError(f"row_count must be between 1 and {MAX_BENCHMARK_ROWS}")
    if profile not in DATASET_PROFILES:
        raise ValueError(f"profile must be one of: {', '.join(DATASET_PROFILES)}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    file_entries: list[dict[str, object]] = []
    injected_issues: list[dict[str, object]] = []
    row_counts = _period_row_counts(row_count)
    first_global_row = 0
    for period, period_rows in zip(PERIODS, row_counts, strict=True):
        if period_rows == 0:
            continue
        if period_rows > MAX_DATA_ROWS_PER_SHEET:
            raise ValueError(f"{period} exceeds the Excel worksheet row limit")
        file_entry, issues = _generate_period_file(
            output_dir=output_dir,
            period=period,
            first_global_row=first_global_row,
            row_count=period_rows,
            rng=rng,
            profile=profile,
        )
        file_entries.append(file_entry)
        injected_issues.extend(issues)
        first_global_row += period_rows

    dimension_files = _generate_dimensions(output_dir)
    ground_truth: dict[str, object] = {
        "version": 1,
        "profile": profile,
        "seed": seed,
        "row_count": row_count,
        "files": file_entries,
        "dimension_files": dimension_files,
        "injected_issues": injected_issues,
    }
    ground_truth_path = output_dir / "ground_truth.json"
    ground_truth_path.write_text(
        json.dumps(ground_truth, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ground_truth_path


def _period_row_counts(row_count: int) -> list[int]:
    base, remainder = divmod(row_count, len(PERIODS))
    return [base + (1 if index < remainder else 0) for index in range(len(PERIODS))]


def _generate_period_file(
    output_dir: Path,
    period: str,
    first_global_row: int,
    row_count: int,
    rng: random.Random,
    profile: Literal["messy", "clean"],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    path = output_dir / f"GL_{period}.xlsx"
    worksheet_name = "Data"
    headers, schema_changes = _headers_for_period(period, profile)
    issues: list[dict[str, object]] = []
    workbook = _new_workbook(path)
    try:
        worksheet = workbook.add_worksheet(worksheet_name)
        worksheet.write(0, 0, f"Synthetic general ledger actuals for {period}")
        worksheet.write(1, 0, "All values are invented for testing.")
        worksheet.write_row(HEADER_ROW - 1, 0, headers)

        previous_row: list[str | None] | None = None
        for local_index in range(row_count):
            global_index = first_global_row + local_index
            row = _new_gl_row(global_index, period, rng)
            issue = _issue_for_row(global_index, local_index) if profile == "messy" else None
            if issue is not None:
                category, column, value = issue
                row = _inject_issue(row, category, value, previous_row)
                issues.append(
                    _issue_record(
                        category=category,
                        column=column,
                        value=(
                            _business_key(row)
                            if category == "duplicate_row"
                            else None
                            if category == "null_required"
                            else value
                        ),
                        filename=path.name,
                        global_index=global_index,
                        row_number=TITLE_ROWS + 1 + local_index + 1,
                    )
                )
            if profile == "messy" and period == "2025-12":
                row = _remove_required_date(row)
            worksheet.write_row(TITLE_ROWS + 1 + local_index, 0, row)
            previous_row = row

        if profile == "messy":
            footer_row = TITLE_ROWS + 1 + row_count
            worksheet.write(footer_row, 0, "TOTAL")
    finally:
        workbook.close()

    file_entry: dict[str, object] = {
        "file": path.name,
        "period": period,
        "sheet": worksheet_name,
        "header_row": HEADER_ROW,
        "footer_rows": FOOTER_ROWS if profile == "messy" else 0,
        "row_count": row_count,
        "schema_changes": schema_changes,
        "expected_file_outcome": "fail_missing_required_column"
        if profile == "messy" and period == "2025-12"
        else "process",
        "expected_warnings": schema_changes["added_columns"],
    }
    return file_entry, issues


def _headers_for_period(
    period: str, profile: Literal["messy", "clean"]
) -> tuple[list[str], dict[str, object]]:
    amount_header = "Amt USD" if profile == "messy" and period >= "2026-01" else "Amount (USD)"
    headers = [
        "Document Number",
        "Line Number",
        "Posting Date",
        "GL Account",
        amount_header,
        "Cost Center",
    ]
    changes: dict[str, object] = {
        "renamed_headers": ["Amount (USD) -> Amt USD"] if amount_header == "Amt USD" else [],
        "added_columns": [],
        "missing_required_columns": [],
    }
    if profile == "messy" and period >= "2026-01":
        headers.append("Region")
        changes["added_columns"] = ["Region"]
    if profile == "messy" and period == "2025-12":
        headers.remove("Posting Date")
        changes["missing_required_columns"] = ["Posting Date"]
    return headers, changes


def _new_gl_row(global_index: int, period: str, rng: random.Random) -> list[str | None]:
    year, month = (int(part) for part in period.split("-"))
    row: list[str | None] = [
        f"DOC-{global_index + 1:08d}",
        "1",
        f"{year:04d}-{month:02d}-{rng.randint(1, 28):02d}",
        f"400{rng.randint(0, 19):02d}",
        f"{rng.randint(-100_000, 100_000) / 100:.2f}",
        f"CC-{rng.randint(1, 30):03d}",
    ]
    if period >= "2026-01":
        row.append(rng.choice(("North", "South", "East", "West")))
    return row


def _issue_for_row(global_index: int, local_index: int) -> tuple[str, str, str] | None:
    offset = global_index % ISSUE_CYCLE_ROWS
    if offset == 500 and local_index == 0:
        return None
    if offset == 501 and local_index == 1:
        return ISSUE_SPECS[500]
    return ISSUE_SPECS.get(offset)


def _inject_issue(
    row: list[str | None],
    category: str,
    value: str,
    previous_row: list[str | None] | None,
) -> list[str | None]:
    if category == "malformed_amount" or category in {
        "accounting_negative",
        "thousands_separator",
    }:
        row[4] = value
    elif category == "null_required":
        row[0] = None
    elif category == "duplicate_row":
        if previous_row is None:
            raise ValueError("Cannot inject a duplicate before the first data row")
        return previous_row.copy()
    return row


def _remove_required_date(row: list[str | None]) -> list[str | None]:
    return [value for index, value in enumerate(row) if index != 2]


def _business_key(row: list[str | None]) -> str:
    return f"{row[0]}|{row[1]}"


def _issue_record(
    category: str,
    column: str,
    value: str | None,
    filename: str,
    global_index: int,
    row_number: int,
) -> dict[str, object]:
    return {
        "category": category,
        "expected_outcome": "reject",
        "reason": category,
        "file": filename,
        "global_row_index": global_index,
        "row_number": row_number,
        "column": column,
        "value": value,
    }


def _generate_dimensions(output_dir: Path) -> list[dict[str, object]]:
    dimensions = (
        (
            "chart_of_accounts.xlsx",
            "Chart of Accounts",
            ("GL Account", "Description"),
            [(f"400{index:02d}", f"Synthetic account {index:02d}") for index in range(20)],
        ),
        (
            "cost_centers.xlsx",
            "Cost Centers",
            ("Cost Center", "Description"),
            [(f"CC-{index:03d}", f"Synthetic cost center {index:03d}") for index in range(1, 31)],
        ),
    )
    entries: list[dict[str, object]] = []
    for filename, title, headers, records in dimensions:
        path = output_dir / filename
        workbook = _new_workbook(path)
        try:
            worksheet = workbook.add_worksheet("Data")
            worksheet.write(0, 0, title)
            worksheet.write_row(1, 0, headers)
            for row_index, record in enumerate(records, start=2):
                worksheet.write_row(row_index, 0, record)
        finally:
            workbook.close()
        entries.append({"file": filename, "row_count": len(records), "sheet": "Data"})
    return entries


def _new_workbook(path: Path) -> _WorkbookWriter:
    return cast(
        _WorkbookWriter,
        xlsxwriter.Workbook(path, {"constant_memory": True}),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rows", type=int, choices=BENCHMARK_SIZES, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--profile", choices=DATASET_PROFILES, default="messy")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        ground_truth_path = generate_dataset(
            args.output_dir,
            args.rows,
            args.seed,
            profile=args.profile,
        )
    except (FileExistsError, OSError, ValueError) as error:
        LOGGER.error("Could not generate synthetic data: %s", error)
        return 1
    LOGGER.info(
        "Generated %s %s rows at %s; ground truth: %s",
        args.rows,
        args.profile,
        args.output_dir,
        ground_truth_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
