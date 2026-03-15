# Dashboard Repo Architecture Note

Date: 2026-03-15

Status: Scratchpad

Purpose:
- keep repo-facing notes about the downstream dashboard architecture
- document the current expected boundary from `model-runner`
- avoid turning this repo into the dashboard implementation home

This file is intentionally downstream-facing and non-authoritative for the dashboard repo.
It exists so this repo can remember what the downstream architecture expects today.

## Current boundary assumptions
The dashboard repo is expected to consume `model-runner` through external interfaces only:
- canonical telemetry JSONL/app export
- optional Prometheus-compatible metrics

It should not import internal modules from this repo as a primary integration path.

## Current architectural shape
The dashboard repo is expected to have three layers.

### 1. Ingestion layer
Consumes telemetry from `model-runner`.

Inputs:
- canonical JSON events, primarily via JSONL sink ingestion
- optional Prometheus scrape data
- optional GPU/system exporter metrics

Responsibilities:
- normalize external input into dashboard-owned read models
- maintain live session state
- persist recent history as needed

### 2. Dashboard service layer
Serves dashboard-facing queries and live updates.

Likely responsibilities:
- session list/detail APIs
- experiment compare APIs
- live subscription fanout
- retention/downsampling policy
- local persistence management

### 3. Web UI layer
Provides the browser experience.

Likely areas:
- overview
- sessions
- compare
- inspect
- logs
- future chat area in the same shell

## Current entity expectations
The dashboard repo should expect these concepts from `model-runner`:
- session
- experiment
- load report
- turn summary
- runtime sample
- log event
- error event

## Current app/API expectations
The dashboard repo should assume:
- events are append-only
- payloads are versioned
- event envelopes include `session_id` and `event_id`
- unknown fields may appear over time
- some metrics are unavailable on some backends

The dashboard should therefore:
- treat missing fields as capability gaps, not hard failures
- clearly distinguish unavailable vs zero
- prefer canonical fields over backend-specific extensions
- use `session_id` for correlation across events
- be ready to use `event_id` for dedup or append-only replay safety when needed

## Current JSONL framing assumptions
The current expected JSONL sink format is:
- one complete event envelope per line
- one single-line JSON object per line
- append-only, no multiline framing

This repo's ingestion path should assume that framing directly.

## Current Prometheus posture
Prometheus is expected to be useful for:
- quick charts
- standard metric collection
- reuse of existing exporter tooling

Prometheus is not expected to be sufficient for:
- turn-level inspection
- knob truth
- logs
- request inspect views
- chat/session semantics

The dashboard repo should therefore treat Prometheus as supplemental, not primary.
The default Prometheus surface is also expected to exclude high-cardinality IDs like `event_id` and `session_id`.
That exclusion applies to Prometheus labels, not to canonical event exports.

## Current runner contract assumption
The current expected `model-runner` MVP boundary is:
- in-process canonical telemetry publisher in the runner
- optional file-backed JSONL sink
- optional Prometheus export, disabled by default

Expected canonical event behavior:
- `load_reported` is merged by `session_id`
- latest known field value wins per field
- partial load facts may arrive over multiple events

This repo should therefore assume:
- runner does not need to expose dashboard-facing HTTP/SSE
- this repo owns live service transport to the browser
- local SSE in `lab-llm` is fed by this repo's ingestion layer, not by a direct runner stream

## Current UI posture
The downstream UI should be:
- observability-first initially
- ready to share a shell with future browser chat
- explicit about live vs completed state
- explicit about unknown/unavailable metrics

## Open notes
- If the dashboard repo needs long-retention storage, that should be solved there, not here.
- If the dashboard repo wants richer compare workflows or annotations, that should be solved there, not here.
- If the telemetry schema changes, this note should only summarize the downstream impact, not restate the full schema.
