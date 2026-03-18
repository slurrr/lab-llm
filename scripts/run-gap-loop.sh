#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ITERATIONS="${1:-$(python "$ROOT_DIR/scripts/coordination_config.py" loop_iterations)}"

for i in $(seq 1 "$ITERATIONS"); do
  echo "== gap loop iteration $i =="
  ./scripts/run-model-runner-gap-pass.sh
  ./scripts/reconcile-gap-ledger.sh

  if grep -q "No eligible upstream gaps found" "$ROOT_DIR/docs/coordination/current_gap_slice.md"; then
    echo "No eligible upstream gaps remain."
    break
  fi

  if python "$ROOT_DIR/scripts/coordination_state.py" check-loop-stop; then
    :
  else
    echo "Loop stopped by guardrail."
    break
  fi
done

echo "Gap loop complete."
