# Current State Audit

Date: 2026-03-16

This file is a blunt assessment of the current dashboard against `docs/successful_lab.md`.

## Latest evidence reviewed
- `frontend/artifacts/latest.png`
- `frontend/artifacts/history-2026-03-16T08-06-19-037Z.png`
- `frontend/artifacts/api-status-20260316T080618Z.json`
- `frontend/artifacts/api-sessions-20260316T080618Z.json`
- `frontend/artifacts/api-session-detail-20260316T080618Z.json`
- `docs/coordination/inbox/response.md`
- `docs/coordination/inbox/artifacts/hf-qwen35-9b-sess_d8f3abe025ee4201abab2d30fa06188f.jsonl`

## What already exists
- fixture and JSONL ingestion
- local REST/SSE service
- session list/detail shell
- basic throughput/GPU/KV charts
- load/runtime/turn/log/inspect surfaces

## What is already directionally correct
- the repo split is correct
- the dashboard is built around operator-facing sessions, not generic metrics alone
- projected truth is available in-place
- upstream canonical telemetry has started to improve for newly verified sessions:
  - model display name is split from model path
  - requested runtime intent is split from confirmed runtime truth, with mismatches called out explicitly
  - activity state is split from session lifecycle status
  - KV cache unavailability is explicit instead of silent omission
  - throughput now carries trust/measurement-state semantics
  - completed-turn throughput now separates raw completion speed from effective request speed
  - turn-finished timing can include TTFT plus honest decode latency
  - turn stop reason can include source attribution
  - log messages can arrive without duplicated timestamp/source prefixes
  - GPU samples can include utilization/power/temperature plus explicit diagnosis incompleteness

## What is still failing usefulness
- the audited frontend/API is still serving older path-only and numeric-only projections even though the newer verified finished session `sess_d8f3abe025ee4201abab2d30fa06188f` is already present in the sessions list
- the selected audited session `sess_c7acaf69b1cc451081d7038203fd9c1e` started at `2026-03-16T06:01:57.731Z`, before the upstream verification run at `2026-03-16T08:03:29.432Z`, so the dashboard is still showing a pre-fix projection for the main detail pane
- too many summaries are still thin wrappers around incomplete telemetry
- model identity is still not trustworthy on the rendered surface
- the top summary still says `Latest event Not yet` even though the audited detail payload has `session.last_event_at: 2026-03-16T08:06:17.491Z` and `latest_runtime.ts: 2026-03-16T08:06:17.488Z`
- tok/s is still visible before its trustworthiness is clear
- session lifecycle and current activity are still collapsed into one `running/live` story
- GPU and KV cards still spend primary space on unavailable signals
- the recent-turn strip still shows `TTFT Unavailable` and does not surface stop reason or plain-language timing
- the rendered log rows are still duplicated/noisy, and the audited detail payload does not expose log entries for cross-checking
- the inspect path stops at projected truth instead of exposing the canonical event fields that now matter
- source/path status is still unavailable on the audited backend
- the session list is still too ambiguous to help an operator pick the right run quickly, even though the sessions API already has timestamps and error state
- bottleneck diagnosis is not possible yet
- several important question areas from `docs/successful_lab.md` have no meaningful surface at all

## Main conclusion
The current app is now split between better upstream telemetry and an older dashboard projection. The newest verified runner artifact proves real improvement in canonical telemetry, but the newest audited `lab-llm` surface still does not carry forward most of that truth.

That means the next useful slices should still be chosen from the gap ledger, with emphasis on read-model/API adoption of canonical identity, runtime-truth mismatch semantics, activity state, KV/throughput measurement semantics, richer turn timing, log normalization, GPU live signals, honest freshness/source states, and a less ambiguous session list.
