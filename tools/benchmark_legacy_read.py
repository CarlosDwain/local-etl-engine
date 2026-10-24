"""Run a limited legacy Excel-to-SQLite read-stage benchmark in an isolated copy."""

import argparse
import csv
import hashlib
import json
import logging
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

from tools.generate_data import BENCHMARK_SIZES

LOGGER = logging.getLogger("etl.legacy_benchmark")
BENCHMARK_ROW_COUNTS = BENCHMARK_SIZES[:2]
REPETITIONS = {100_000: 5, 1_000_000: 3}
CSV_FIELDS = (
    "dataset_rows",
    "run",
    "is_warmup",
    "stage_wall_seconds",
    "stage_cpu_seconds",
    "peak_rss_bytes",
    "input_files",
    "successful_files",
    "failed_files",
    "rows_loaded",
    "expected_rows",
    "row_count_matches",
    "process_exit_code",
    "process_wall_seconds",
    "database_bytes",
    "log_file",
)

_CHILD_RUNNER = r"""
import json
import pathlib
import sys
import threading
import time

import psutil

legacy_root = pathlib.Path(sys.argv[1])
run_dir = pathlib.Path(sys.argv[2])
input_dir = pathlib.Path(sys.argv[3])
sys.path.insert(0, str(legacy_root / "src"))

from classes.Config import Config
from classes.DataSources import DataSources
from classes.Database import Database
from pipelines.read.ETL import ETL

configuration_dir = legacy_root / "resources" / "configuration"
Config(str(configuration_dir / "app.json"))
DataSources(str(configuration_dir / "data-sources.json"))
Config.get_ignore()
files = sorted(input_dir.glob("GL_*.xlsx"))
statuses = []
process = psutil.Process()
peak_rss = [process.memory_info().rss]
stop_sampling = threading.Event()

def sample_memory():
    while not stop_sampling.wait(0.1):
        peak_rss[0] = max(peak_rss[0], process.memory_info().rss)

sampler = threading.Thread(target=sample_memory, daemon=True)
sampler.start()
started_wall = time.perf_counter()
started_cpu = time.process_time()
Database(str(run_dir / ".app" / ".warehouse.db"))
Database.load_schema(str(configuration_dir / "schema.json"))
success = []
for source_file in files:
    etl = ETL("GL Actuals", str(source_file))
    statuses.append((source_file.name, "[ETL] - Reading"))
    etl.read()
    statuses.append((source_file.name, "[ETL] - Transforming"))
    etl.transform()
    statuses.append((source_file.name, "[ETL] - Saving"))
    etl.load()
    if not etl.is_failed:
        success.append(source_file)
        statuses.append((source_file.name, "Done"))
    else:
        statuses.append((source_file.name, "[ETL] - FAILED"))
    relative_path = source_file.relative_to(input_dir).as_posix()
    if not etl.is_failed and not relative_path.startswith("."):
        Config.add_ignore([relative_path])
stage_wall = time.perf_counter() - started_wall
stage_cpu = time.process_time() - started_cpu
stop_sampling.set()
sampler.join()
peak_rss[0] = max(peak_rss[0], process.memory_info().rss)
connection = Database.get_connection()
rows_loaded = connection.cursor().execute("SELECT COUNT(*) FROM gl_actuals").fetchone()[0]
Database.close_connection()
sys.stdout.write("BENCHMARK_RESULT=" + json.dumps({
    "stage_wall_seconds": stage_wall,
    "stage_cpu_seconds": stage_cpu,
    "peak_rss_bytes": peak_rss[0],
    "input_files": len(files),
    "successful_files": len(success),
    "failed_files": len(files) - len(success),
    "rows_loaded": rows_loaded,
    "statuses": len(statuses),
}))
"""


def _dataset_info(input_dir: Path) -> tuple[int, list[dict[str, object]]]:
    ground_truth_path = input_dir / "ground_truth.json"
    ground_truth = cast(
        dict[str, object], json.loads(ground_truth_path.read_text(encoding="utf-8"))
    )
    if ground_truth.get("profile") != "clean":
        raise ValueError(f"{input_dir.name} must use the clean generator profile")
    row_count = ground_truth.get("row_count")
    files = ground_truth.get("files")
    if not isinstance(row_count, int) or not isinstance(files, list):
        raise ValueError(f"Invalid ground truth in {ground_truth_path.name}")

    entries: list[dict[str, object]] = []
    for file_value in files:
        file_entry = cast(dict[str, object], file_value)
        filename = file_entry.get("file")
        expected_rows = file_entry.get("row_count")
        if not isinstance(filename, str) or not isinstance(expected_rows, int):
            raise ValueError(f"Invalid file entry in {ground_truth_path.name}")
        source_path = input_dir / filename
        entries.append(
            {
                "file": filename,
                "period": file_entry.get("period"),
                "row_count": expected_rows,
                "size_bytes": source_path.stat().st_size,
                "sha256": _sha256(source_path),
            }
        )
    if _total_rows(entries) != row_count:
        raise ValueError(f"Ground-truth file counts do not add up for {input_dir.name}")
    return row_count, entries


def _total_rows(entries: list[dict[str, object]]) -> int:
    total = 0
    for entry in entries:
        row_count = entry.get("row_count")
        if not isinstance(row_count, int):
            raise ValueError("Input manifest contains an invalid row count")
        total += row_count
    return total


def _source_configuration() -> dict[str, object]:
    return {
        "GL Actuals": {
            "table": "gl_actuals",
            "append": True,
            "header": 2,
            "sheet_name": "Data",
            "required_columns": [
                "Document Number",
                "Line Number",
                "Posting Date",
                "GL Account",
                "Amount (USD)",
                "Cost Center",
            ],
            "filter": {"persist": [], "keep": [], "remove": []},
        }
    }


def _schema_configuration() -> dict[str, object]:
    columns = {
        "file_id": {"type": "VARCHAR(34)"},
        "document_number": {
            "column": ["Document Number"],
            "type": "VARCHAR(100)",
            "nullable": False,
        },
        "line_number": {
            "column": ["Line Number"],
            "type": "INTEGER",
            "nullable": False,
        },
        "posting_date": {
            "column": ["Posting Date"],
            "type": "DATE",
            "nullable": False,
        },
        "gl_account": {
            "column": ["GL Account"],
            "type": "VARCHAR(20)",
            "nullable": False,
        },
        "amount_usd": {
            "column": ["Amount (USD)"],
            "type": "FLOAT",
            "nullable": False,
        },
        "cost_center": {
            "column": ["Cost Center"],
            "type": "VARCHAR(20)",
            "nullable": False,
        },
    }
    return {"gl_actuals": columns}


def _write_legacy_configuration(legacy_root: Path) -> None:
    configuration_dir = legacy_root / "resources" / "configuration"
    configuration_dir.mkdir(parents=True, exist_ok=True)
    (configuration_dir / "app.json").write_text(
        json.dumps({"base_path": ""}, indent=2) + "\n",
        encoding="utf-8",
    )
    (configuration_dir / "data-sources.json").write_text(
        json.dumps(_source_configuration(), indent=2) + "\n",
        encoding="utf-8",
    )
    (configuration_dir / "schema.json").write_text(
        json.dumps(_schema_configuration(), indent=2) + "\n",
        encoding="utf-8",
    )


def _legacy_environment(
    conda_executable: Path, conda_environment: str
) -> tuple[dict[str, object], dict[str, str]]:
    code = (
        "import json, os, sys, pandas, numpy, openpyxl, psutil; "
        "sys.stdout.write(json.dumps({'versions': {'python': sys.version, "
        "'pandas': pandas.__version__, 'numpy': numpy.__version__, "
        "'openpyxl': openpyxl.__version__, 'psutil': psutil.__version__}, "
        "'environment': {key: os.environ.get(key, '') for key in "
        "('PATH', 'CONDA_PREFIX', 'CONDA_DEFAULT_ENV')}}))"
    )
    completed = subprocess.run(
        [str(conda_executable), "run", "-n", conda_environment, "python", "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    probe = cast(dict[str, object], json.loads(completed.stdout))
    versions = cast(dict[str, object], probe["versions"])
    environment = cast(dict[str, str], probe["environment"])
    return versions, environment


def _run_child(
    python_executable: Path,
    legacy_root: Path,
    run_dir: Path,
    input_dir: Path,
    timeout_seconds: int,
    environment: dict[str, str],
) -> tuple[dict[str, object] | None, int | None, float, str, str, bool]:
    app_config = legacy_root / "resources" / "configuration" / "app.json"
    app_config.write_text(
        json.dumps({"base_path": str(run_dir)}, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / ".app").mkdir(parents=True)
    (run_dir / ".app" / ".warehouse.db").touch()

    started = time.perf_counter()
    process = subprocess.Popen(
        [
            str(python_executable),
            "-c",
            _CHILD_RUNNER,
            str(legacy_root),
            str(run_dir),
            str(input_dir),
        ],
        cwd=legacy_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, **environment},
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        stop_command = f"Stop-Process -Id {process.pid} -Force -ErrorAction SilentlyContinue"
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", stop_command],
            check=False,
            capture_output=True,
            text=True,
        )
        stdout, stderr = process.communicate()
    process_wall_seconds = time.perf_counter() - started
    output: dict[str, object] | None = None
    for line in stdout.splitlines():
        if line.startswith("BENCHMARK_RESULT="):
            output = cast(dict[str, object], json.loads(line.removeprefix("BENCHMARK_RESULT=")))
    return output, process.returncode, process_wall_seconds, stdout, stderr, timed_out


def _benchmark(
    benchmark_root: Path,
    legacy_root: Path,
    python_executable: Path,
    conda_executable: Path,
    conda_environment: str,
    timeout_seconds: int,
) -> Path:
    results_dir = benchmark_root / "results" / "legacy-read"
    run_root = benchmark_root / "runs" / "legacy-read"
    if results_dir.exists() or run_root.exists():
        raise FileExistsError("Benchmark result or run folder already exists; use a fresh folder.")

    _write_legacy_configuration(legacy_root)
    result_parent = results_dir.parent
    result_parent.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir()
    run_root.mkdir(parents=True)

    manifest: dict[str, object] = {}
    datasets: dict[int, tuple[Path, list[dict[str, object]]]] = {}
    for row_count in BENCHMARK_ROW_COUNTS:
        input_dir = benchmark_root / "input" / f"clean-{row_count // 1000}k"
        if row_count == 1_000_000:
            input_dir = benchmark_root / "input" / "clean-1m"
        rows, entries = _dataset_info(input_dir)
        if rows != row_count:
            raise ValueError(f"Expected {row_count} rows, found {rows} in {input_dir.name}")
        datasets[row_count] = (input_dir, entries)
        manifest[input_dir.name] = {"row_count": rows, "files": entries}

    (results_dir / "input-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    legacy_versions, legacy_env = _legacy_environment(conda_executable, conda_environment)
    environment = {
        "benchmark_scope": "legacy read-stage ingestion baseline (synthetic GL)",
        "timed_work": (
            "Legacy ETL.read/transform/load loop, with GL's unregistered transform as a no-op"
        ),
        "controller_import_limitation": (
            "ProcessController import fails because the mart registry references a missing module; "
            "the harness calls the read-loop operations through the legacy ETL class"
        ),
        "excluded_work": (
            "dataset generation, imports, app startup, database row-count verification"
        ),
        "legacy_code_sha256": _tree_sha256(legacy_root / "src"),
        "legacy_runtime": legacy_versions,
        "host": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
            "python": sys.version,
            "disk_free_bytes": shutil.disk_usage(benchmark_root).free,
        },
        "warmup_runs_per_size": 1,
        "measured_runs": {str(size): REPETITIONS[size] for size in BENCHMARK_ROW_COUNTS},
        "timeout_seconds": timeout_seconds,
        "datasets": {
            "100000": "input/clean-100k",
            "1000000": "input/clean-1m",
        },
    }
    (results_dir / "environment.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    csv_path = results_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_stream:
        writer = csv.DictWriter(csv_stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        benchmark_failed = False
        for row_count in BENCHMARK_ROW_COUNTS:
            input_dir, entries = datasets[row_count]
            expected_rows = _total_rows(entries)
            logs_dir = results_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            repetitions = REPETITIONS[row_count]
            for run_number in range(repetitions + 1):
                is_warmup = run_number == 0
                label = "warmup" if is_warmup else f"run-{run_number:02d}"
                run_dir = run_root / str(row_count) / label
                run_dir.mkdir(parents=True)
                (
                    output,
                    exit_code,
                    process_wall_seconds,
                    stdout,
                    stderr,
                    timed_out,
                ) = _run_child(
                    python_executable=python_executable,
                    legacy_root=legacy_root,
                    run_dir=run_dir,
                    input_dir=input_dir,
                    timeout_seconds=timeout_seconds,
                    environment=legacy_env,
                )
                log_path = logs_dir / f"{row_count}-{label}.log"
                log_path.write_text(
                    f"exit_code={exit_code}\ntimed_out={timed_out}\n\n"
                    f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}",
                    encoding="utf-8",
                )
                row: dict[str, object] = {
                    "dataset_rows": row_count,
                    "run": label,
                    "is_warmup": is_warmup,
                    "process_exit_code": exit_code,
                    "process_wall_seconds": round(process_wall_seconds, 6),
                    "database_bytes": (run_dir / ".app" / ".warehouse.db").stat().st_size,
                    "log_file": str(log_path.relative_to(results_dir)),
                }
                if output is not None:
                    loaded_rows = output.get("rows_loaded")
                    row.update(
                        {
                            "stage_wall_seconds": output.get("stage_wall_seconds"),
                            "stage_cpu_seconds": output.get("stage_cpu_seconds"),
                            "peak_rss_bytes": output.get("peak_rss_bytes"),
                            "input_files": output.get("input_files"),
                            "successful_files": output.get("successful_files"),
                            "failed_files": output.get("failed_files"),
                            "rows_loaded": loaded_rows,
                            "expected_rows": expected_rows,
                            "row_count_matches": loaded_rows == expected_rows,
                        }
                    )
                else:
                    row.update(
                        {
                            "stage_wall_seconds": "",
                            "stage_cpu_seconds": "",
                            "peak_rss_bytes": "",
                            "input_files": len(entries),
                            "successful_files": "",
                            "failed_files": "",
                            "rows_loaded": "",
                            "expected_rows": expected_rows,
                            "row_count_matches": False,
                        }
                    )
                writer.writerow(row)
                csv_stream.flush()
                LOGGER.info(
                    "%s %s: exit=%s rows=%s/%s stage_seconds=%s timed_out=%s",
                    row_count,
                    label,
                    exit_code,
                    row.get("rows_loaded", "unknown"),
                    expected_rows,
                    row.get("stage_wall_seconds", "unknown"),
                    timed_out,
                )
                if (
                    timed_out
                    or exit_code != 0
                    or output is None
                    or row.get("row_count_matches") is not True
                ):
                    benchmark_failed = True
                    break
            if benchmark_failed:
                break
    _write_summary(results_dir, csv_path)
    summary = cast(
        dict[str, object],
        json.loads((results_dir / "summary.json").read_text(encoding="utf-8")),
    )
    dataset_summaries = cast(dict[str, dict[str, object]], summary["datasets"])
    if not all(
        dataset.get("all_runs_loaded_expected_row_count") is True
        for dataset in dataset_summaries.values()
    ):
        raise RuntimeError(f"Benchmark incomplete; review {results_dir}")
    return csv_path


def _write_summary(results_dir: Path, csv_path: Path) -> None:
    with csv_path.open(newline="", encoding="utf-8") as csv_stream:
        rows = list(csv.DictReader(csv_stream))
    summary: dict[str, object] = {
        "benchmark_scope": "legacy read-stage ingestion baseline (synthetic GL)",
        "end_to_end_comparison": False,
        "datasets": {},
    }
    dataset_summaries: dict[str, object] = {}
    for row_count in BENCHMARK_ROW_COUNTS:
        measured = [
            row
            for row in rows
            if row["dataset_rows"] == str(row_count) and row["is_warmup"] == "False"
        ]
        valid = [
            row
            for row in measured
            if row["process_exit_code"] == "0"
            and row["row_count_matches"] == "True"
            and row["stage_wall_seconds"]
            and row["stage_cpu_seconds"]
        ]
        timings = [float(row["stage_wall_seconds"]) for row in valid]
        dataset_summaries[str(row_count)] = {
            "measured_runs": len(measured),
            "valid_runs": len(valid),
            "expected_runs": REPETITIONS[row_count],
            "all_runs_loaded_expected_row_count": len(valid) == REPETITIONS[row_count],
            "wall_seconds": {
                "median": statistics.median(timings) if timings else None,
                "min": min(timings) if timings else None,
                "max": max(timings) if timings else None,
            },
            "loaded_row_counts": [int(row["rows_loaded"]) for row in valid],
        }
    summary["datasets"] = dataset_summaries
    (results_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(bytes.fromhex(_sha256(path)))
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--legacy-python", type=Path, required=True)
    parser.add_argument("--conda-executable", type=Path, required=True)
    parser.add_argument("--conda-environment", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    args = parser.parse_args()
    benchmark_root = args.benchmark_root.resolve()
    legacy_root = benchmark_root / "legacy"
    python_executable = args.legacy_python.resolve()
    conda_executable = args.conda_executable.resolve()
    if args.timeout_seconds < 1:
        parser.error("--timeout-seconds must be positive")
    if (
        not legacy_root.is_dir()
        or not python_executable.is_file()
        or not conda_executable.is_file()
    ):
        parser.error("legacy sandbox and Python/Conda executables must exist")
    if any(
        "onedrive" in part.lower() or "sharepoint" in part.lower() for part in benchmark_root.parts
    ):
        parser.error("benchmark root must be outside OneDrive and SharePoint")
    try:
        result = _benchmark(
            benchmark_root=benchmark_root,
            legacy_root=legacy_root,
            python_executable=python_executable,
            conda_executable=conda_executable,
            conda_environment=args.conda_environment,
            timeout_seconds=args.timeout_seconds,
        )
    except (
        FileExistsError,
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        LOGGER.error("Legacy benchmark failed: %s", error)
        return 1
    LOGGER.info("Legacy benchmark results written to %s", result)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
