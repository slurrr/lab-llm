#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_RUNNER_ROOT="${MODEL_RUNNER_ROOT:-$(python "$ROOT_DIR/scripts/coordination_config.py" model_runner_root)}"
DEST_DIR="$MODEL_RUNNER_ROOT/docs/downstream/lab_llm"
COUNT="${1:-$(python "$ROOT_DIR/scripts/coordination_config.py" gap_slice_count)}"

python "$ROOT_DIR/scripts/gap_slice.py" --count "$COUNT" >/tmp/lab-llm-gap-slice-path.txt
SLICE_PATH="$(cat /tmp/lab-llm-gap-slice-path.txt)"
python "$ROOT_DIR/scripts/verification_target.py" --slice "$ROOT_DIR/$SLICE_PATH" >/tmp/lab-llm-verification-target.txt
VERIFY_PATH="$(cat /tmp/lab-llm-verification-target.txt)"
python "$ROOT_DIR/scripts/coordination_state.py" record-selection --slice "$ROOT_DIR/$SLICE_PATH"

mkdir -p "$DEST_DIR/artifacts"

cp "$ROOT_DIR/docs/gap_ledger.md" "$DEST_DIR/gap_ledger.md"
cp "$ROOT_DIR/docs/operator_questions.md" "$DEST_DIR/operator_questions.md"
cp "$ROOT_DIR/docs/current_state_audit.md" "$DEST_DIR/current_state_audit.md"
cp "$ROOT_DIR/$SLICE_PATH" "$DEST_DIR/current_gap_slice.md"
cp "$ROOT_DIR/$VERIFY_PATH" "$DEST_DIR/verification_target.md"

if [[ -f "$ROOT_DIR/frontend/artifacts/latest.png" ]]; then
  cp "$ROOT_DIR/frontend/artifacts/latest.png" "$DEST_DIR/artifacts/latest.png"
fi

latest_meta="$(ls -1t "$ROOT_DIR"/frontend/artifacts/audit-meta-*.txt 2>/dev/null | head -n 1 || true)"
if [[ -n "$latest_meta" ]]; then
  cp "$latest_meta" "$DEST_DIR/artifacts/"
  while IFS='=' read -r key value; do
    case "$key" in
      status_path|sessions_path|detail_path|screenshot_path)
        if [[ -f "$value" ]]; then
          cp "$value" "$DEST_DIR/artifacts/"
        fi
        ;;
    esac
  done <"$latest_meta"
fi

cat >"$DEST_DIR/README.md" <<'EOF'
# lab-llm downstream bundle

Source of truth lives in `/home/poop/projects/lab-llm`.

Files here are mirrored for upstream telemetry work in `model-runner`.
Do not edit the mirrored gap ledger here; update the source repo instead.

Use:
- `current_gap_slice.md` for the current 3-5 gap work slice
- `verification_target.md` for the default telemetry-producing verification target
- `response.md` to report what upstream changed
EOF

if [[ ! -f "$DEST_DIR/response.md" ]]; then
  cat >"$DEST_DIR/response.md" <<'EOF'
# Upstream Response

Date:

## Addressed gaps
- 

## Gaps attempted but not closed
- 

## Gaps blocked
- 

## Telemetry changes
- 

## Verification run
- 

## Evidence
- 
EOF
fi

echo "$DEST_DIR"
