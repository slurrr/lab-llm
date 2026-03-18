#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_RUNNER_ROOT="${MODEL_RUNNER_ROOT:-$(python "$ROOT_DIR/scripts/coordination_config.py" model_runner_root)}"
COUNT="${1:-$(python "$ROOT_DIR/scripts/coordination_config.py" gap_slice_count)}"

./scripts/push-gap-slice.sh "$COUNT" >/tmp/lab-llm-push-dest.txt
DEST_DIR="$(cat /tmp/lab-llm-push-dest.txt)"

cat <<EOF | codex exec --dangerously-bypass-approvals-and-sandbox -C "$MODEL_RUNNER_ROOT" -
Read:
- docs/downstream/lab_llm/current_gap_slice.md
- docs/downstream/lab_llm/gap_ledger.md
- docs/downstream/lab_llm/operator_questions.md
- docs/downstream/lab_llm/verification_target.md

Implement only the selected upstream gaps from current_gap_slice.md.

Rules:
- treat lab-llm's mirrored files as downstream contract input, not files to edit
- edit model-runner code and docs as needed
- update docs/downstream/lab_llm/response.md with:
  - addressed gaps
  - gaps attempted but not closed
  - gaps blocked
  - telemetry/schema/emission changes
  - verification run
  - evidence paths
- do not claim a gap is fixed unless the code and emitted telemetry semantics really changed
- prefer telemetry truth improvements over dashboard-specific workarounds
- if your changes affect telemetry schema, emission semantics, backend adapters, sink wiring, or any field used by the selected gaps, run a real telemetry-producing load plus at least one short generation before finishing
- if your changes affect model identity, startup/load semantics, or runtime-truth emission, do not verify against a stale already-running process
- if the runnable path depends on a build/install step, rebuild from the latest source before starting the fresh verification run
- verification must come from a freshly started run that is actually using the changed code, not from an already-running app or pre-change built artifact
- choose the verification target from verification_target.md unless the selected gaps are clearly backend-specific and a different existing backend/model path is a better match
- inspect the repo for an existing runner/dev/test command before inventing a new one; choose the narrowest command that loads the target model/backend and writes telemetry
- record the exact fresh-code step you ran, the exact run command you ran, whether you killed/restarted the target, the backend/model you exercised, the fresh session id produced after the code changes, and where the resulting telemetry evidence was written

When done, leave the repo in a usable state for downstream audit.
EOF

echo "$DEST_DIR"
