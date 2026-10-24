# Build plan

Work one step at a time. Each step has a "done when". Tick the box when it is true.
Current step: **Step 2: Synthetic data and baseline**.

## What the scaffold already contains

Domain models (`Period`, `Layer`, `Contract`, results, errors), all ports, the `Stage` template, the
`PipelineRunner`, `ManifestService`, `DriftDetector`, `LocalFolderSource`, `DuckDbEngine`, config
loading with working-folder validation, the YAML contract loader, a Typer CLI shell, the container,
in-memory fakes, tests, and all architecture gates. The remaining pipeline stages and adapters are
stubs marked `TODO(step N)`.

## Steps

- [x] **Step 1: Skeleton complete.** Implement `YamlContractRepository` (Pydantic schema -> domain `Contract`, `_defaults.yaml` merge) and load `contracts/gl_actuals.yaml`. *Done when:* the example contract loads and a malformed one fails with a readable `ContractError`.
- [x] **Step 2: Synthetic data and baseline.** `tools/generate_data.py` with ground-truth file, sizes 100K / 1M / 5M, split into files under the 1,048,576-row Excel limit. *Done when:* a "before" benchmark exists. **Completed:** synthetic clean GL legacy read-stage baseline at 100K and 1M; 5M generation is supported but was not benchmarked. The like-for-like new-backend comparison is deferred until Step 3. See [the baseline report](../benchmarks/legacy-read/README.md).
- [ ] **Step 3: Vertical slice for one source.** `CalamineExcelReader`, `ParquetLayerStore`, `DuckDbManifestStore`, ingest, staging (`TRY_CAST`, rejects), one mart, export. *Done when:* a re-run with no file changes does nothing, and changing one file replaces only its partition.
- [ ] **Step 4: Second implementations.** CSV reader, Parquet exporter, console and queue reporters, stubbed `GraphApiSource`. *Done when:* each port has two implementations or a documented reason it does not.
- [ ] **Step 5: Widen features.** Drift report, rejects report, `QualityGate` and checks, generated keys, reject thresholds, layout versioning, archive. *Done when:* ground-truth tests pass with every seeded error type.
- [ ] **Step 6: UI and packaging.** Tkinter presenter and view, then `pyinstaller --onedir`, tested on a clean Windows machine without Python. *Done when:* a non-technical user can run it from a synced folder.
- [ ] **Step 7: Later.** `dbt-core` + `dbt-duckdb`, lineage diagram, optional Streamlit dashboard, Graph API fetching.

## Out of scope for now

dbt, Streamlit dashboard, Graph API fetching (use a OneDrive-synced folder), row-level upserts, cancel button, corrections file, code signing.
