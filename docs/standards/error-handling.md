# Error handling standards

| Level | Example | Behavior |
|---|---|---|
| Row | failed cast, null in required column, duplicate key | Row goes to rejects with reason, file, and row number. The rest of the file loads |
| File | unreadable, password protected, missing sheet, missing required column, zero rows | Whole file fails, nothing written for it, other files continue |
| File threshold | more than X% of rows rejected (set in contract) | Treat the file as failed |
| Data check | control total mismatch, unexpected row-count drop | Stop before marts |
| Run | unexpected crash | Atomic writes mean no half-written partitions |

- **E-1 Expected outcomes are returned, not raised.** A bad row or drifted file becomes a result object (`StageResult`, `DriftReport`, `RejectRow`).
- **E-2 Unexpected failures raise a subclass of `EtlError`:** `ConfigError`, `ContractError`, `IngestError`, `QualityGateError`. Catch them at the runner boundary and turn them into a readable message.
- **E-3 No stack traces in the UI.** Log the traceback to the log file; show the human a short message and what to do.
- **E-4 A failed file stays flagged** in the manifest and is retried on the next run. Nothing disappears silently.
- **E-5 Every run ends with reports:** a drift report and a rejects report (file, row, column, bad value, reason), with the amount excluded from totals where relevant.
- **E-6 Never swallow exceptions.** No bare `except`. Catch the specific type and either handle it or re-raise as an `EtlError`.
- **E-7 Error messages say what happened, where (file, row, column), and what to try next.**
