# ADR 0003: Data source contracts as YAML validated by Pydantic

- Status: accepted

## Context
Excel sources drift silently (renamed headers, moved rows). Schema knowledge is currently scattered.

## Decision
One YAML contract per source plus `_defaults.yaml`. Validated by Pydantic at startup, mapped into
frozen domain dataclasses. Drift behavior is declared per contract. Git holds the history.

## Consequences
Schema changes are reviewable text diffs. Pydantic stays at the boundary (rule C-4), so the domain
remains dependency-free.
