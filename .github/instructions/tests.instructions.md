---
applyTo: "tests/**"
---
# Test rules

- Unit tests use in-memory fakes from `tests/fakes.py`. No disk, no DuckDB (T-2).
- Integration tests are marked `@pytest.mark.integration` and use real adapters with `tmp_path` (T-3).
- Arrange / act / assert, one behaviour per test, names like `test_<unit>_<behaviour>` (T-4).
- Synthetic data only. Never copy real client rows into fixtures (D-14).
- A bug fix starts with a failing test that reproduces it (T-6).
- When the synthetic generator exists, assert rejects equal the ground-truth file exactly (T-7).
