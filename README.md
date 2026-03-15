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
- `docs/decisions/`
- `docs/specs/`

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
