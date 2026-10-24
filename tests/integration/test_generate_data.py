import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest
from tools.generate_data import (
    BENCHMARK_SIZES,
    MAX_DATA_ROWS_PER_SHEET,
    _period_row_counts,
    generate_dataset,
)

pytestmark = pytest.mark.integration


def test_generate_dataset_writes_seeded_workbooks_and_ground_truth(tmp_path: Path) -> None:
    output_dir = tmp_path / "synthetic"

    ground_truth_path = generate_dataset(output_dir, row_count=600, seed=123)

    ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    fact_files = sorted(output_dir.glob("GL_*.xlsx"))
    assert len(fact_files) == 12
    assert ground_truth["row_count"] == 600
    assert sum(file_info["row_count"] for file_info in ground_truth["files"]) == 600
    assert {issue["category"] for issue in ground_truth["injected_issues"]} == {
        "malformed_amount",
        "accounting_negative",
        "thousands_separator",
        "null_required",
        "duplicate_row",
    }
    assert (output_dir / "chart_of_accounts.xlsx").is_file()
    assert (output_dir / "cost_centers.xlsx").is_file()
    files_by_period = {entry["period"]: entry for entry in ground_truth["files"]}
    assert files_by_period["2026-01"]["schema_changes"] == {
        "renamed_headers": ["Amount (USD) -> Amt USD"],
        "added_columns": ["Region"],
        "missing_required_columns": [],
    }
    assert files_by_period["2025-12"]["schema_changes"]["missing_required_columns"] == [
        "Posting Date"
    ]
    issue_by_category = {issue["category"]: issue for issue in ground_truth["injected_issues"]}
    assert issue_by_category["null_required"]["value"] is None
    assert issue_by_category["duplicate_row"]["column"] == "_business_key"


def test_generate_dataset_is_deterministic_for_the_same_seed(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first_ground_truth = generate_dataset(first_dir, row_count=600, seed=987)
    second_ground_truth = generate_dataset(second_dir, row_count=600, seed=987)

    assert first_ground_truth.read_bytes() == second_ground_truth.read_bytes()
    first_file = first_dir / "GL_2025-07.xlsx"
    second_file = second_dir / "GL_2025-07.xlsx"
    with (
        zipfile.ZipFile(first_file) as first_archive,
        zipfile.ZipFile(second_file) as second_archive,
    ):
        assert first_archive.read("xl/worksheets/sheet1.xml") == second_archive.read(
            "xl/worksheets/sheet1.xml"
        )


def test_generate_dataset_clean_profile_has_no_injected_errors_or_schema_drift(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "clean"

    ground_truth_path = generate_dataset(output_dir, row_count=600, seed=123, profile="clean")

    ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    assert ground_truth["profile"] == "clean"
    assert ground_truth["injected_issues"] == []
    expected_schema_changes: dict[str, list[str]] = {
        "renamed_headers": [],
        "added_columns": [],
        "missing_required_columns": [],
    }
    assert all(
        entry["schema_changes"] == expected_schema_changes for entry in ground_truth["files"]
    )
    assert all(entry["footer_rows"] == 0 for entry in ground_truth["files"])
    with (
        zipfile.ZipFile(output_dir / "GL_2025-07.xlsx") as first_archive,
        zipfile.ZipFile(output_dir / "GL_2026-01.xlsx") as later_archive,
    ):
        first_sheet = ElementTree.fromstring(first_archive.read("xl/worksheets/sheet1.xml"))
        later_sheet = ElementTree.fromstring(later_archive.read("xl/worksheets/sheet1.xml"))

    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    first_rows = first_sheet.findall(".//main:sheetData/main:row", namespace)
    later_rows = later_sheet.findall(".//main:sheetData/main:row", namespace)
    assert len(first_rows[2]) == 6
    assert len(later_rows[2]) == 6
    assert all(len(row) == 6 for row in first_rows[3:-1])
    assert len(first_rows) == ground_truth["files"][0]["row_count"] + 3


def test_generated_workbook_has_excel_safe_rows_and_contract_header(tmp_path: Path) -> None:
    output_dir = tmp_path / "synthetic"
    generate_dataset(output_dir, row_count=600, seed=123)

    with zipfile.ZipFile(output_dir / "GL_2025-07.xlsx") as archive:
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows = sheet.findall(".//main:sheetData/main:row", namespace)
    ground_truth = json.loads((output_dir / "ground_truth.json").read_text(encoding="utf-8"))
    expected_data_rows = next(
        entry["row_count"] for entry in ground_truth["files"] if entry["period"] == "2025-07"
    )
    assert len(rows) == expected_data_rows + 4
    assert len(rows) <= MAX_DATA_ROWS_PER_SHEET + 4
    assert rows[0].attrib["r"] == "1"
    assert rows[2].attrib["r"] == "3"
    assert rows[-1].attrib["r"] == str(len(rows))


def test_generated_schema_changes_are_present_in_the_workbooks(tmp_path: Path) -> None:
    output_dir = tmp_path / "synthetic"
    generate_dataset(output_dir, row_count=600, seed=123)

    with (
        zipfile.ZipFile(output_dir / "GL_2026-01.xlsx") as changed_archive,
        zipfile.ZipFile(output_dir / "GL_2025-12.xlsx") as missing_archive,
    ):
        changed_sheet = ElementTree.fromstring(changed_archive.read("xl/worksheets/sheet1.xml"))
        missing_sheet = ElementTree.fromstring(missing_archive.read("xl/worksheets/sheet1.xml"))

    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    changed_headers = [
        cell.findtext(".//main:t", namespaces=namespace)
        for cell in changed_sheet.findall(".//main:sheetData/main:row", namespace)[2]
    ]
    missing_headers = [
        cell.findtext(".//main:t", namespaces=namespace)
        for cell in missing_sheet.findall(".//main:sheetData/main:row", namespace)[2]
    ]
    assert "Amt USD" in changed_headers
    assert "Region" in changed_headers
    assert "Posting Date" not in missing_headers


def test_benchmark_sizes_split_below_the_excel_limit() -> None:
    for row_count in BENCHMARK_SIZES:
        period_counts = _period_row_counts(row_count)

        assert sum(period_counts) == row_count
        assert max(period_counts) <= MAX_DATA_ROWS_PER_SHEET


def test_generate_dataset_rejects_existing_output_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "synthetic"
    output_dir.mkdir()
    existing_file = output_dir / "keep.txt"
    existing_file.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="not empty"):
        generate_dataset(output_dir, row_count=600, seed=123)

    assert existing_file.read_text(encoding="utf-8") == "keep"


def test_generate_dataset_rejects_row_counts_outside_supported_range(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="between 1 and 5000000"):
        generate_dataset(tmp_path / "synthetic", row_count=5_000_001, seed=123)
