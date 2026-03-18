# Coordination Protocol

This repo owns the gap ledger.

`model-runner` owns upstream telemetry implementation.

The file-based loop is:
1. Audit the dashboard in `lab-llm`.
2. Update `docs/gap_ledger.md`.
3. Generate a 3-5 gap slice.
4. Push the mirrored bundle into `model-runner`.
5. `model-runner` implements the slice, runs a real telemetry-producing verification path when telemetry behavior changed, and writes `docs/downstream/lab_llm/response.md`.
6. Pull the response back into `lab-llm`.
7. Re-run the dashboard audit, preferring the verified session id or evidence target from the upstream response when present.
8. Only if the audit shows a genuine local projection/wiring issue, let `lab-llm` make the minimal read-model/API/UI change needed to expose the new telemetry truth.
9. Audit again, update the ledger, and repeat.

## Commands
Generate and push the current slice to `model-runner`:
```bash
./scripts/push-gap-slice.sh
```

Pull the latest `model-runner` response back here:
```bash
./scripts/pull-model-runner-response.sh
```

Run one upstream implementation pass automatically:
```bash
./scripts/run-model-runner-gap-pass.sh
```

Pull response, rerun audit, and update the ledger here:
```bash
./scripts/reconcile-gap-ledger.sh
```

Run a multi-iteration loop:
```bash
./scripts/run-gap-loop.sh
```

All defaults come from:
```bash
docs/coordination.defaults.toml
```

Bootstrap from:
```bash
cp docs/coordination.defaults.example.toml docs/coordination.defaults.toml
```

Optional manual steering lives in:
```bash
docs/coordination/focus.txt
```

Bootstrap from:
```bash
cp docs/coordination/focus.example.txt docs/coordination/focus.txt
```

If that file contains one or more gap ids, the slice generator will prefer those gaps before normal ranking.
This is the intended way to force a narrow proof pass without disabling automation.

That file currently defines:
- `model_runner_root`
- `telemetry_jsonl`
- `api_base`
- `dashboard_url`
- `gap_slice_count`
- `loop_iterations`
- `verification_policy`

## Practical limit
This loop can automate most coordination work, but it still depends on:
- `model-runner` being able to make real upstream fixes without interactive blockers
- a live or restartable dashboard/backend target for audit
- telemetry changes being observable in audit artifacts

It should reduce manual passes heavily, but “wake up with no gaps” is only realistic when the remaining gaps are actually automatable and verifiable from live artifacts.

## Unattended mode
`run-gap-loop.sh` uses `codex exec --dangerously-bypass-approvals-and-sandbox` for the outer loop so it does not stop for approvals overnight.

That is intentional for unattended local automation.
Use it only in the repo/workspace you are comfortable granting that level of autonomy.

## Canonical locations
Source of truth in this repo:
- `docs/gap_ledger.md`
- `docs/operator_questions.md`
- `docs/current_state_audit.md`
- `docs/coordination.defaults.example.toml`
- `docs/coordination/focus.example.txt`

Mirrored bundle in `model-runner`:
- `docs/downstream/lab_llm/`

Response file expected from `model-runner`:
- `docs/downstream/lab_llm/response.md`

Verification target mirrored into `model-runner`:
- `docs/downstream/lab_llm/verification_target.md`
