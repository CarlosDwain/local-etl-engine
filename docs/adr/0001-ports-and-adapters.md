# ADR 0001: Ports and adapters architecture

- Status: accepted

## Context
The current tool mixes UI, cleaning, and storage, which makes it slow to change and hard to test. This
project is also meant to teach the team modern engineering practice.

## Decision
Use a layered ports-and-adapters design. The application depends on small `Protocol` ports; adapters
(DuckDB, Excel, Tkinter) plug in from outside. Only `container.py` builds adapters. `import-linter`
enforces the dependency rule.

## Consequences
More files and indirection than a script, in exchange for fakes-based unit tests and easy swaps (for
example local folder to Graph API). Abstractions are only added when a realistic second implementation
exists (rule A-7).
