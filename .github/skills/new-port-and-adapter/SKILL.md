---
name: new-port-and-adapter
description: Add a new port and its first adapter following the architecture rules
disable-model-invocation: true
---
Add a new port and adapter. Inputs: the port's job, and the technology for the first adapter.

1. Read `docs/standards/architecture.md` and `docs/standards/coding-standards.md`.
2. Confirm rule A-7: name the realistic second implementation. If none exists, stop and ask.
3. Add a small `Protocol` to `src/etl/application/ports.py`.
4. Add the adapter in the right `src/etl/infrastructure/` subfolder.
5. Wire it in `src/etl/container.py` with an explicit import (C-10).
6. Add an in-memory fake to `tests/fakes.py`, unit tests using the fake, and an integration test for the real adapter.
7. Run `python scripts/check.py` and report rule IDs applied.
