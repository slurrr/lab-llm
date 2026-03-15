# 0001 - Consume runner telemetry through external interfaces

Date: 2026-03-15

## Context
This repo exists because the browser dashboard is a separate product from the runner/backend workspace.

The runner repo owns:
- model execution
- backend adapters
- telemetry production
- export boundaries

If this repo imports runner internals directly, the separation collapses and both repos become harder to evolve independently.

## Decision
`lab-llm` will consume runner data through external interfaces only.

Primary boundaries:
1. app-facing JSON/event telemetry
2. optional Prometheus-compatible metrics

This repo should not use direct imports from the runner repo as its primary integration model.

## Consequences
- Ingestion code here should assume versioned external payloads.
- Missing fields and unknown event types must be handled gracefully.
- Read models in this repo may differ from the producer schema, but the producer schema remains upstream truth.
- Local development should be possible against recorded event fixtures as well as a live runner.
