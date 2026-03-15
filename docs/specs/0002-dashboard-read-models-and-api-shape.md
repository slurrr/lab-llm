#!/usr/bin/env markdown
# Spec: Dashboard read models and API shape

Date: 2026-03-15

Status: Draft

Related decisions:
- `docs/decisions/0001-external-telemetry-boundary.md`

Related note:
- `docs/dashboard_repo_architecture.md`

## Context / problem
The producer schema is event-oriented.
The dashboard needs query-friendly read models.

If we pass producer events straight through to every UI surface, the frontend becomes coupled to ingestion details and hard to evolve.

## Goals
- Define dashboard-owned read models derived from upstream telemetry.
- Keep the UI API simple and session-centric.
- Preserve upstream truth while allowing dashboard-friendly shaping.

## Non-goals
- Redefining the producer schema.
- Finalizing persistent storage technology.

## Read models
### Session summary
Fields:
- `session_id`
- `status`
- `backend_name`
- `resolved_model_id`
- `started_at`
- `ended_at`
- `last_event_at`
- `has_errors`

### Session detail
Fields:
- `session`
- `load_report`
- `latest_runtime`
- `recent_turns`
- `recent_logs`
- `inspect`

### Turn row
Fields:
- `turn_id`
- `started_at`
- `ended_at`
- `prompt_tokens`
- `completion_tokens`
- `request_latency_seconds`
- `time_to_first_token_seconds`
- `stop_reason`

### Inspect view
Fields:
- `load_truth`
- `generation_truth`
- `backend_extensions`

## API shape
Minimum endpoints or equivalents:
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `GET /api/sessions/{session_id}/turns`
- `GET /api/sessions/{session_id}/logs`
- `GET /api/sessions/{session_id}/inspect`
- live subscription for active session updates

The exact transport can change, but these query shapes should remain stable.

## API rules
- Prefer aggregated read models over raw event replay in UI handlers.
- Missing data should remain missing, not coerced to zero.
- Backend-specific extensions should be grouped clearly and not mixed into canonical fields.
- Timestamps should be UTC ISO 8601.
- Browser-facing live updates are owned by this repo even if upstream ingestion is file-backed.
- Session/read-model assembly should rely on canonical event exports, not Prometheus labels, for event identity and session correlation.
- `load_report` should be treated as a field-wise merged view built from one or more `load_reported` events for a session.

## Acceptance criteria
- The service layer can expose a stable session-centric API without leaking ingestion internals.
- The UI can render overview and session detail screens using these read models.
