---
name: new-source-contract
description: Create a data source contract plus staging SQL for a new Excel source
disable-model-invocation: true
---
Create a contract for a new source. I will provide headers, the header row, junk rows above or below, and a few fake sample rows.

1. Read `docs/standards/data-standards.md` (D-9 to D-11) and `.github/instructions/contracts.instructions.md`.
2. Create `contracts/<source>.yaml`, reusing `_defaults.yaml`. Declare only the columns we use; add `aliases` for known header variants.
3. Define the business key, or set `key_strategy: generated` and explain why.
4. Create `sql/staging/stg_<source>.sql` using `TRY_CAST` and keeping lineage columns.
5. Add a unit test that loads the contract and checks drift detection for a missing required column.
6. Run `python scripts/check.py` and report rule IDs applied.
