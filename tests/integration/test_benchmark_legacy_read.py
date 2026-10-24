import csv
import json
from pathlib import Path

import pytest
from tools.benchmark_legacy_read import CSV_FIELDS, _write_summary

pytestmark = pytest.mark.integration


def test_benchmark_summary_marks_failed_run_incomplete(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    csv_path = results_dir / "results.csv"
    row = dict.fromkeys(CSV_FIELDS, "")
    row.update(
        {
            "dataset_rows": "100000",
            "run": "run-01",
            "is_warmup": "False",
            "stage_wall_seconds": "",
            "stage_cpu_seconds": "",
            "rows_loaded": "",
            "row_count_matches": "False",
            "process_exit_code": "1",
        }
    )
    with csv_path.open("w", newline="", encoding="utf-8") as csv_stream:
        writer = csv.DictWriter(csv_stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow(row)

    _write_summary(results_dir, csv_path)

    summary = json.loads((results_dir / "summary.json").read_text(encoding="utf-8"))
    failed_dataset = summary["datasets"]["100000"]
    assert failed_dataset["valid_runs"] == 0
    assert failed_dataset["all_runs_loaded_expected_row_count"] is False
