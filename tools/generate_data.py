"""Synthetic data generator. TODO(step 2).

Spec (see docs/standards/testing-standards.md T-7 and data-standards D-14):
- Sources: gl_actuals (fact), chart_of_accounts and cost_centers (dimensions).
- Sizes: 100K / 1M / 5M rows, seedable. Split files by period (Excel limit is 1,048,576 rows).
- Inject: title rows above header, totals row at bottom, text in amount columns, "(500)" negatives,
  thousands separators, duplicate rows, null required fields, a renamed header and a new column from
  2026-01, and one file missing a required column.
- Write ground_truth.json listing every injected error so tests can assert rejects match exactly.
"""


def main() -> int:
    raise NotImplementedError("TODO(step 2)")


if __name__ == "__main__":
    raise SystemExit(main())
