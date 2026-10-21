---
applyTo: "contracts/**"
---
# Contract rules

- One YAML per source. Shared settings go in `_defaults.yaml` (D-9).
- Declare the columns we use (required and optional). List legitimate header variants under `aliases`.
- Always declare `keys` (business key) or set `key_strategy: generated` (D-10).
- Types: `string`, `date`, `int`, `decimal(p,s)`, `bool`. Casting happens in staging, not at ingest.
- Contracts contain structure and rules only. Never put real values or client names in them.
- Bump `version` when the layout changes. Git history is the version control (D-11).
