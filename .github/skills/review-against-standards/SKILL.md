---
name: review-against-standards
description: Review the current changes against every project standard
disable-model-invocation: true
---
Review the staged and unstaged changes against `docs/standards/*.md` and `.github/copilot-instructions.md`.

For each finding, give the rule ID, the file and line, and a concrete fix. Check in this order:
architecture (A-*), coding (C-*), data (D-*), errors (E-*), tests (T-*), then the Definition of Done.
Run `python scripts/check.py` and include its result. Do not change code unless I ask; only report.
