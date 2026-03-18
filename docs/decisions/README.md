# Decisions

Architectural decisions for `lab-llm`.

## Index

| ID | Title | Summary |
|---|---|---|
| 0001 | Consume runner telemetry through external interfaces | This repo consumes canonical telemetry via external app/metrics boundaries rather than importing runner internals. |
| 0002 | Build an observability-first web product with room for chat later | The primary UX is runtime observability now, with a shared browser shell that can host chat later. |
| 0003 | The dashboard repo owns the telemetry gap ledger | `lab-llm` defines operator-facing telemetry gaps and holds `model-runner` accountable for closing them. |

## Format

- One file per decision: `0001-<slug>.md`, `0002-<slug>.md`, ...
- Keep them practical: context -> decision -> consequences.
- Use dates in ISO format (`YYYY-MM-DD`).
