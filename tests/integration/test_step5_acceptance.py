import json
from pathlib import Path

import pytest
from tools.generate_data import generate_dataset

from etl.application.stages.base import RunOptions
from etl.config import AppConfig
from etl.container import build_runner

pytestmark = pytest.mark.integration


def test_messy_ground_truth_runs_through_quality_pipeline(tmp_path: Path) -> None:
    landing = tmp_path / "landing"
    generate_dataset(landing, row_count=600, seed=123, profile="messy")
    repository_root = Path(__file__).parents[2]
    config = AppConfig(
        source_dir=landing,
        output_dir=tmp_path / "output",
        contracts_dir=repository_root / "contracts",
        working_dir=tmp_path / "work",
    )

    summary = build_runner(config).run(RunOptions())
    ground_truth = json.loads((landing / "ground_truth.json").read_text(encoding="utf-8"))

    assert summary.ok
    assert summary.files_failed == 1
    assert summary.rows_rejected == 4
    assert len(ground_truth["injected_issues"]) == 5
    assert not (landing / "GL_2025-07.xlsx").exists()
