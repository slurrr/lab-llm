#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TELEMETRY_JSONL="${TELEMETRY_JSONL:-$(python "$ROOT_DIR/scripts/coordination_config.py" telemetry_jsonl)}"
API_BASE="${API_BASE:-$(python "$ROOT_DIR/scripts/coordination_config.py" api_base)}"
URL="${URL:-$(python "$ROOT_DIR/scripts/coordination_config.py" dashboard_url)}"
COUNT="${COUNT:-$(python "$ROOT_DIR/scripts/coordination_config.py" gap_slice_count)}"

./scripts/pull-model-runner-response.sh >/tmp/lab-llm-pull-dest.txt

if [[ -f "$ROOT_DIR/docs/coordination/inbox/response.md" ]]; then
  python "$ROOT_DIR/scripts/coordination_state.py" record-response --response "$ROOT_DIR/docs/coordination/inbox/response.md"
fi

pre_meta_path="$(./scripts/audit-dashboard.sh --api-base "$API_BASE" --url "$URL")"
python "$ROOT_DIR/scripts/coordination_state.py" record-audit --meta "$pre_meta_path"

cat <<'EOF' | codex exec --dangerously-bypass-approvals-and-sandbox -C "$ROOT_DIR" -
Read:
- docs/gap_ledger.md
- docs/current_state_audit.md
- docs/operator_questions.md
- docs/coordination/inbox/response.md if present
- docs/coordination/inbox/current_gap_slice.md if present
- docs/coordination/state.json
- the newest files under frontend/artifacts/

Tasks:
1. Only if the latest audit proves that upstream truth is available but hidden by `lab-llm` read-model/API/UI behavior, implement the minimal local change needed to expose that truth.
2. Update docs/gap_ledger.md based on the latest audit artifacts and upstream response.
3. Close or downgrade only the gaps that are genuinely improved by the new telemetry/dashboard evidence.
4. Add any new obvious operator-usefulness gaps revealed by the audit.
5. Update docs/current_state_audit.md to reflect the latest state.
6. Do not close a gap solely because upstream claims it is fixed; require matching audit evidence or make the gap partial/pending-verification instead.

Rules:
- be strict about telemetry truth
- do not close a gap just because upstream said it worked
- rely on audit evidence and current rendered behavior
- keep the gap ledger as the source of truth
- do not make speculative `lab-llm` code changes just to "help the loop complete"
- only touch `lab-llm` code when the audit shows a real local wiring/projection/adoption problem
EOF

post_meta_path="$(./scripts/audit-dashboard.sh --api-base "$API_BASE" --url "$URL")"
python "$ROOT_DIR/scripts/coordination_state.py" record-audit --meta "$post_meta_path"

python "$ROOT_DIR/scripts/gap_slice.py" --count "$COUNT"
python "$ROOT_DIR/scripts/verification_target.py" --slice "$ROOT_DIR/docs/coordination/current_gap_slice.md"
