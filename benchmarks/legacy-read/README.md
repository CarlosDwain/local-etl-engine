# Legacy read-stage ingestion baseline (synthetic GL)

This is a legacy-only baseline for the Excel read, no-op transform, and SQLite load path using
synthetic GL workbooks. It is **not** an end-to-end ETL benchmark and does not compare the legacy
backend with the new backend. The new-backend comparison is deferred until Step 3 implements
equivalent ingestion.

## Results

One warm-up was discarded for each size. The measured runs used a fresh subprocess and SQLite
database for every attempt.

| Input rows | Measured runs | Loaded rows per run | Median stage wall time | Min–max stage wall time | Median stage CPU time | Maximum sampled RSS |
|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 5 | 100,000 | 6.901 s | 6.650–7.752 s | 6.578 s | 139,505,664 bytes |
| 1,000,000 | 3 | 1,000,000 | 87.623 s | 66.116–89.250 s | 85.203 s | 207,011,840 bytes |

Every measured run exited successfully, processed all 12 input files, and loaded the expected
number of rows into the single configured `gl_actuals` table. Per-run details are in
[results.csv](./results.csv); aggregate validation is in [summary.json](./summary.json).
The 1M runs varied substantially, so treat these as a recorded baseline rather than a stable
throughput claim.

## Method and limitations

- Inputs were generated with seed `42` using the generator's `clean` profile. Each dataset has 12
  monthly Excel files, consistent headers, no injected errors or schema drift, and no footer rows.
  [input-manifest.json](./input-manifest.json) records each workbook's SHA-256, byte size, and row
  count. The input workbooks themselves are not committed.
- Only the legacy `src` tree was copied into `%LOCALAPPDATA%\FIA-ETL-Benchmark\legacy`; existing
  legacy data and configuration were not copied. A sanitized GL source and SQLite schema were
  generated in that sandbox. The original and sandbox each had 43 Python files with the same
  source-tree SHA-256 (`4fc90d4ec6dd8dd8f2e7909ab0f305153722605f9d055e18cc1c37769c51d246`).
- `ProcessController` could not be imported because its mart registry references a missing
  `promise_to_pay` module. To avoid changing the legacy copy, the harness calls the legacy `ETL`
  class's per-file `read`, `transform`, and `load` operations directly. The configured GL source has
  no registered transformer, so `transform` is a no-op. This is a harnessed read-stage path, not
  the normal GUI/controller execution.
- Timing starts before the SQLite database/schema setup and ends after the per-file ETL loop and
  ignore-file updates. Imports, application startup, data generation, and the final database
  row-count verification are excluded. The row count is verified after the timed section.
- The available legacy environment was Python 3.7.9, pandas 1.3.5, NumPy 1.18.4, openpyxl 3.0.4,
  and psutil 5.7.3. The legacy requirements pin pandas 1.0.4, so this result does not represent
  that pinned dependency set.
- The host was Windows 11 with 8 logical CPUs; the runtime reports the processor as
  `Intel64 Family 6 Model 189 Stepping 1, GenuineIntel`. Detailed runtime and host information is
  in [environment.json](./environment.json). Power-plan, antivirus, and disk-type state were not
  recorded. Repeats used the same files and may benefit from the Windows file cache.
- The 5M synthetic-data size is supported by the generator but was not run for this legacy baseline.
  These measurements must not be presented as a legacy-vs-new speedup or an end-to-end result.

Raw subprocess output is preserved in [logs/](./logs/).
