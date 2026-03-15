#!/usr/bin/env markdown
# Spec: Observability dashboard MVP

Date: 2026-03-15

Status: Draft

Related decisions:
- `docs/decisions/0001-external-telemetry-boundary.md`
- `docs/decisions/0002-observability-first-shared-shell.md`

Related note:
- `docs/dashboard_repo_architecture.md`

## Context / problem
This repo needs a usable first product shape, not just a pile of future ideas.

The MVP needs to prove:
- telemetry from the runner can be ingested cleanly
- live session state can be rendered in a browser
- the dashboard can show runtime truth better than terminal scrollback

## Goals
- Build a browser-based observability MVP.
- Support live and recent session inspection.
- Keep the architecture compatible with a future chat area in the same shell.
- Make missing metrics explicit rather than hiding capability gaps.

## Non-goals
- Building browser chat in v1.
- Long-retention analytics.
- Full experiment notebook features.
- Supporting every telemetry producer on day one.

## Product areas
The app shell should reserve space for:
- `Observe`
- `Chat` placeholder only

V1 implements `Observe` only.

## MVP architecture
### 1. Ingestion layer
Responsibilities:
- consume canonical telemetry events from JSONL sink output
- map producer payloads into dashboard read models
- maintain current live session state

Ingestion assumptions:
- each JSONL line is one complete event envelope
- `session_id` is always available for correlation
- `event_id` remains available in the canonical event path even if excluded from default Prometheus labels
- `load_reported` may arrive partially and multiple times per session

### 2. Service layer
Responsibilities:
- expose session list/detail APIs
- expose recent turn summaries
- expose inspect/log views
- expose live updates for active sessions

### 3. Web UI
Responsibilities:
- render overview and session detail pages
- distinguish live, finished, and error sessions
- visualize unavailable metrics explicitly

## MVP screens
### Overview
Shows:
- active sessions
- recent completed sessions
- basic machine/runtime health when available

### Session detail
Shows:
- load summary
- throughput and latency
- GPU/memory/KV charts
- turn list
- logs
- inspect panel for request/generation truth

## MVP data expectations
The UI should be able to render from:
- session events
- load reports
- turn summaries
- runtime samples
- log events
- error events

The initial live path should assume:
- `model-runner` writes canonical JSONL telemetry
- `lab-llm` ingests it and exposes browser-facing REST/SSE
- Prometheus support may exist upstream, but app state should not depend on Prometheus carrying `session_id` or `event_id`

## Acceptance criteria
- A live runner session can appear in the dashboard.
- A user can open a session detail view and inspect load truth, runtime charts, logs, and recent turns.
- Unavailable metrics are shown explicitly.
- The app structure leaves a clean path for a future `Chat` area without rewriting the shell.
