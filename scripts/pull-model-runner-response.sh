#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_RUNNER_ROOT="${MODEL_RUNNER_ROOT:-$(python "$ROOT_DIR/scripts/coordination_config.py" model_runner_root)}"
SRC_DIR="$MODEL_RUNNER_ROOT/docs/downstream/lab_llm"
DEST_DIR="$ROOT_DIR/docs/coordination/inbox"

mkdir -p "$DEST_DIR"

for file in response.md current_gap_slice.md README.md; do
  if [[ -f "$SRC_DIR/$file" ]]; then
    cp "$SRC_DIR/$file" "$DEST_DIR/"
  fi
done

if [[ -d "$SRC_DIR/artifacts" ]]; then
  mkdir -p "$DEST_DIR/artifacts"
  cp -f "$SRC_DIR"/artifacts/* "$DEST_DIR/artifacts/" 2>/dev/null || true
fi

echo "$DEST_DIR"
