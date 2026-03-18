# lab-llm

`lab-llm` is the browser-side observability and control surface for a local LLM lab.

This repo is intentionally separate from the runner/backend repo.
Its job is to:
- consume telemetry from the runner
- visualize runtime behavior
- compare sessions and experiments
- grow toward a shared browser surface for observability first, chat later

## Current posture
This repo starts as a dashboard product, not a model runner.

That means:
- no backend execution logic should be duplicated here
- `model-runner` remains the telemetry producer
- this repo owns ingestion, read models, dashboard APIs, SSE, and browser UX

The current architecture notes live in:
- `docs/dashboard_repo_architecture.md`
- `docs/gap_ledger.md`
- `docs/current_state_audit.md`
- `docs/operator_questions.md`
- `docs/coordination_protocol.md`
- `docs/decisions/`
- `docs/specs/`

## Product accountability
This repo owns the operator-facing telemetry gap ledger.

That means:
- this repo defines what the dashboard still cannot answer
- this repo records which upstream telemetry gaps are blocking usefulness
- `model-runner` remains accountable for closing upstream telemetry truth gaps

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install ruff pyright pytest python-dotenv
cd frontend && npm install && cd ..
```

## Checks
```bash
./scripts/dev.sh
./scripts/check-quick.sh
./scripts/check-full.sh
```

`pyright` is intentionally not in the default local loop.

## Dev
Backend with fixture replay:
```bash
./scripts/dev-backend.sh --fixtures fixtures/telemetry/sample_session.jsonl
```

Backend ingesting `model-runner` JSONL telemetry:
```bash
./scripts/dev-backend.sh --telemetry-jsonl /path/to/model-runner-telemetry.jsonl
```

Frontend:
```bash
./scripts/dev-frontend.sh
```

Integrated build served by Python:
```bash
cd frontend && npm run build && cd ..
./scripts/dev-backend.sh --no-replay-fixtures
```

## Coordination
Push the current 3-5 upstream gap slice into `model-runner`:
```bash
./scripts/push-gap-slice.sh 5
```

Pull the latest upstream response back into this repo:
```bash
./scripts/pull-model-runner-response.sh
```

Run one upstream implementation pass automatically:
```bash
./scripts/run-model-runner-gap-pass.sh
```

Run the recursive loop:
```bash
./scripts/run-gap-loop.sh
```

Loop defaults live in:
```bash
docs/coordination.defaults.toml
```

Start from:
```bash
cp docs/coordination.defaults.example.toml docs/coordination.defaults.toml
```

Loop state lives in:
```bash
docs/coordination/state.json
```

Optional slice focus lives in:
```bash
docs/coordination/focus.txt
```

Start from:
```bash
cp docs/coordination/focus.example.txt docs/coordination/focus.txt
```

Add one `GAP-...` id per line to steer the next slice toward a narrow issue.

The upstream mirror also includes a generated verification target so `model-runner` can run a real telemetry-producing command after emission changes instead of claiming fixes without evidence.

## Dashboard Audit
Single-command audit bundle:
```bash
./scripts/audit-dashboard.sh
```

If the backend is not already running:
```bash
./scripts/audit-dashboard.sh --start-backend --telemetry-jsonl /path/to/model-runner-telemetry.jsonl
```

Artifacts are written under `frontend/artifacts/`:
- `latest.png`
- `history-<timestamp>.png`
- `api-status-<timestamp>.json`
- `api-sessions-<timestamp>.json`
- `api-session-detail-<timestamp>.json`
- `audit-meta-<timestamp>.txt`
