# Testing standards

- **T-1 Test pyramid.** Many unit tests (fast, fakes), fewer integration tests (real adapters), a few end-to-end runs on synthetic data.
- **T-2 Unit tests use in-memory fakes** from `tests/fakes.py`. No disk, no DuckDB. This is why ports exist.
- **T-3 Integration tests** are marked `@pytest.mark.integration`, use real adapters, and `tmp_path` for files.
- **T-4 Arrange / act / assert.** One behaviour per test. Names: `test_<unit>_<behaviour>`.
- **T-5 Every public function or class has tests** for the happy path, a boundary, and a failure.
- **T-6 A bug fix starts with a failing test** that reproduces it.
- **T-7 Ground truth.** The synthetic generator writes a file listing every injected error. Pipeline tests assert rejects equal that list exactly.
- **T-8 Synthetic data only.** No real client rows in fixtures.
- **T-9 Tests are deterministic.** Seed randomness, inject clocks, avoid sleeping.
- **T-10 Never weaken or delete a test to make the build pass.** Fix the cause or ask.

```
uv run pytest -q                      # everything
uv run pytest -m "not integration"    # fast unit tests only
```
