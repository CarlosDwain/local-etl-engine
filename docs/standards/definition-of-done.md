# Definition of done

A task is done only when every box is true. Copilot must walk this list before declaring completion.

- [ ] Works on the current step in `docs/build-plan.md` and does not start later steps
- [ ] Layering respected (A-*): `uv run lint-imports` passes
- [ ] Typed and lint clean (C-*): `mypy --strict` and ruff pass
- [ ] Tests added or updated (T-*): unit with fakes; integration if an adapter changed
- [ ] `uv run python scripts/check.py` passes with no gate skipped or weakened
- [ ] No hardcoded paths, thresholds, or SQL strings (C-11, C-12)
- [ ] Errors follow E-*: expected outcomes returned, unexpected ones raised as `EtlError` subclasses
- [ ] No real data introduced (D-14)
- [ ] Docs updated if behavior or a standard changed; ADR added for any significant decision
- [ ] `docs/build-plan.md` checkbox updated
- [ ] Reply lists the rule IDs that shaped the change and anything to review
