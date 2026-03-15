# Plan: Establish the First Real Frontend Stack for lab-llm

## Summary

Adopt a lightweight but durable frontend baseline:

- Preact + TypeScript + Vite for the UI shell
- uPlot for realtime time-series charts
- SSE for first-pass live telemetry updates
- hand-rolled CSS, no Tailwind or component kit
- Python service continues to own ingestion and API/read-model logic
- Vite runs as the frontend dev server; Python serves built assets in the integrated path

Local checks should stay loose while the product shape is still emerging:

- default local check path: Ruff + tests
- pyright moves out of the default developer loop into an explicit full or ci path
- do not tighten typing/lint gates yet; let the architecture reveal where stronger constraints are actually valuable

## Implementation Changes

### Tooling and repo structure

- Add a frontend workspace under a dedicated directory such as frontend/.
- Initialize a Vite + Preact + TypeScript app there.
- Keep the current Python app as the backend/service layer and make the integration boundary explicit:
    - Python owns telemetry ingestion, read models, and session-centric APIs
    - frontend owns rendering, interaction state, and live dashboard behavior
- Set up the integrated hosting model now:
    - frontend dev: Vite dev server
    - integrated app: Python serves the built frontend assets
- Structure the backend so full separation remains possible later:
    - no frontend-only logic in Python templates
    - no frontend imports from Python internals beyond HTTP/SSE API usage

### Local checks and scripts

- Replace the current all-in-one dev check posture with tiered scripts:
    - quick: Ruff + pytest only
    - full: Ruff + pytest + pyright
- Update scripts/dev.sh to run the quick path only.
- Add a separate explicit script for the full path so static typing is available when wanted but not required every turn.
- Keep pyright configured, but treat it as advisory until the backend/frontend interfaces stabilize.

### Frontend app shape

- Build the app around a small shared shell with:
    - Observe as the only active area
    - Chat reserved as a nav placeholder only
- Use a minimal state/data approach:
    - direct fetches for initial page data
    - a small client-side store for selected session and live updates
    - no heavy global state library unless the app proves it needs one
- Start without a router framework; use a simple route structure only if more than overview/session detail appears.
- Keep styling hand-rolled and intentional:
    - shared CSS variables
    - a few layout primitives
    - no utility framework lock-in

### Realtime data flow

- `model-runner` is expected to produce canonical telemetry and optional JSONL sinks, not browser-facing HTTP/SSE.
- `lab-llm` owns the live service layer for the browser:
    - ingest JSONL telemetry
    - expose REST for initial load
    - expose SSE for live updates
- First-pass client flow:
    - fetch session list and selected session detail via REST
    - subscribe to `lab-llm` SSE for live updates
    - patch the in-memory client state incrementally as events arrive
- Preserve a future upgrade path to WebSockets by isolating the client subscription layer behind a small transport abstraction.

### Charts and UI behavior

- Use uPlot for runtime time-series panels first.
- Start with charts where realtime matters most:
    - throughput
    - latency
    - GPU/memory
    - KV cache
- Keep interaction minimal in v1:
    - live updating
    - hover inspection
    - simple toggles for visible series if needed
- Avoid overbuilding chart controls until real usage reveals them.
- Render unavailable metrics explicitly rather than faking zeros or omitting panels silently.

### Backend adjustments to support the frontend

- Keep the current in-memory read-model store, but formalize the service outputs around the documented session-centric API.
- Add an SSE broadcaster hooked to the same store/event path the REST API reads from.
- Keep fixture-driven bootstrapping so the frontend can be built against recorded telemetry without a live runner.
- Ensure the backend can run in two modes:
    - fixture/demo mode for dashboard development
    - live-ingestion mode later without changing the frontend contract

## Public Interfaces / Contracts

    - session detail
    - logs
    - inspect
- Add one SSE stream endpoint for live telemetry-derived updates.
- SSE payloads should use stable event names aligned with dashboard read-model changes, not raw internal implementation details.
- The frontend should depend only on HTTP/SSE contracts so the backend can later be split into a separate service if needed.

## Test Plan

- Backend tests:
    - fixture ingestion still builds correct read models
    - REST endpoints still return session/detail/log/turn/inspect data
    - SSE endpoint emits valid event frames for session/runtime/log/turn updates
- Frontend tests:
    - overview renders fixture-backed session data
    - session detail renders load truth, latest runtime, turns, and logs
    - SSE updates patch the visible session state correctly
    - unavailable metrics render as unavailable, not zero
- Integration checks:
    - frontend dev server can call the Python API in development
    - built frontend assets can be served by Python in the integrated path

## Assumptions and Defaults

- Frontend framework: Preact + TypeScript + Vite
- Charting: uPlot
- Realtime transport: SSE first, with a clean future path to WebSockets
- Styling: hand-rolled CSS
- Hosting model: Vite dev server in development, Python serves built assets in the integrated path
- Local check posture: quick by default, pyright only in full/CI
- Architecture should not be over-locked yet; keep boundaries clean and thin so the product can reveal what it wants to be
before stricter conventions are imposed
