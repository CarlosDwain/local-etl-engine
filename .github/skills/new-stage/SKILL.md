---
name: new-stage
description: Implement a pipeline stage using the Stage template method
disable-model-invocation: true
---
Implement or complete a pipeline stage.

1. Read `docs/standards/architecture.md` (A-8), `docs/standards/error-handling.md`, and the current step in `docs/build-plan.md`.
2. Subclass `Stage` in `src/etl/application/stages/`. Implement `plan` and `execute` only; use `validate` and `commit` hooks when needed.
3. Receive ports through the constructor. Do not import any adapter.
4. Return a `StageResult`. Expected problems (bad rows, drifted files) become results, not exceptions.
5. Add unit tests with fakes, covering the happy path, a row-level problem, and a file-level failure.
6. Run `python scripts/check.py` and report rule IDs applied.
