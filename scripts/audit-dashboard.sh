#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
ARTIFACT_DIR="$FRONTEND_DIR/artifacts"
URL="http://127.0.0.1:8001/"
API_BASE="http://127.0.0.1:8001"
STATUS_URL="$API_BASE/api/status"
SESSIONS_URL="$API_BASE/api/sessions"
START_BACKEND=0
TELEMETRY_JSONL=""
FIXTURES_PATH=""
REPLAY_FIXTURES=1
REPLAY_SPEED=""
BUILD_FRONTEND=0
PREFERRED_SESSION_ID=""
PREFERRED_SESSION_SOURCE="default"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/audit-dashboard.sh [options]

Options:
  --url <url>                 Dashboard URL. Default: http://127.0.0.1:8001/
  --api-base <url>            API base. Default: http://127.0.0.1:8001
  --start-backend             Start the backend automatically if it is not reachable.
  --telemetry-jsonl <path>    Telemetry JSONL source to pass to dev-backend.sh when starting.
  --fixtures <path>           Fixture JSONL source to pass to dev-backend.sh when starting.
  --no-replay-fixtures        Disable fixture replay when starting backend.
  --replay-speed <n>          Fixture replay speed when starting backend.
  --build-frontend            Build frontend before audit.
  --session-id <id>           Prefer a specific session id for API detail capture and screenshot selection.
  -h, --help                  Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      URL="$2"
      shift 2
      ;;
    --api-base)
      API_BASE="$2"
      shift 2
      ;;
    --start-backend)
      START_BACKEND=1
      shift
      ;;
    --telemetry-jsonl)
      TELEMETRY_JSONL="$2"
      shift 2
      ;;
    --fixtures)
      FIXTURES_PATH="$2"
      shift 2
      ;;
    --no-replay-fixtures)
      REPLAY_FIXTURES=0
      shift
      ;;
    --replay-speed)
      REPLAY_SPEED="$2"
      shift 2
      ;;
    --build-frontend)
      BUILD_FRONTEND=1
      shift
      ;;
    --session-id)
      PREFERRED_SESSION_ID="$2"
      PREFERRED_SESSION_SOURCE="arg"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

STATUS_URL="$API_BASE/api/status"
SESSIONS_URL="$API_BASE/api/sessions"
mkdir -p "$ARTIFACT_DIR"

timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
status_out="$ARTIFACT_DIR/api-status-$timestamp.json"
sessions_out="$ARTIFACT_DIR/api-sessions-$timestamp.json"
detail_out="$ARTIFACT_DIR/api-session-detail-$timestamp.json"
meta_out="$ARTIFACT_DIR/audit-meta-$timestamp.txt"
screenshot_out="$ARTIFACT_DIR/latest.png"

backend_pid=""

health_ok() {
  curl -fsS "$STATUS_URL" >/dev/null 2>&1 || curl -fsS "$SESSIONS_URL" >/dev/null 2>&1
}

detect_verified_session_id() {
  python - "$ROOT_DIR/docs/coordination/inbox/response.md" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("")
    raise SystemExit(0)

text = path.read_text(encoding="utf-8")
match = re.search(r"Verified session id:\s*\n\s*-\s*`([^`]+)`", text)
print(match.group(1) if match else "")
PY
}

append_session_query() {
  python - "$1" "$2" <<'PY'
import sys
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

url = sys.argv[1]
session_id = sys.argv[2]
parts = urlparse(url)
query = dict(parse_qsl(parts.query, keep_blank_values=True))
query["session"] = session_id
print(urlunparse(parts._replace(query=urlencode(query))))
PY
}

cleanup() {
  if [[ -n "$backend_pid" ]]; then
    kill "$backend_pid" >/dev/null 2>&1 || true
    wait "$backend_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ "$BUILD_FRONTEND" -eq 1 ]]; then
  (
    cd "$FRONTEND_DIR"
    npm run build
  )
fi

if ! health_ok; then
  if [[ "$START_BACKEND" -ne 1 ]]; then
    echo "Dashboard backend is not reachable at $STATUS_URL or $SESSIONS_URL" >&2
    echo "Use --start-backend to launch it from this script." >&2
    exit 1
  fi

  backend_args=()
  if [[ -n "$TELEMETRY_JSONL" ]]; then
    backend_args+=(--telemetry-jsonl "$TELEMETRY_JSONL")
  elif [[ -n "$FIXTURES_PATH" ]]; then
    backend_args+=(--fixtures "$FIXTURES_PATH")
    if [[ "$REPLAY_FIXTURES" -eq 0 ]]; then
      backend_args+=(--no-replay-fixtures)
    fi
    if [[ -n "$REPLAY_SPEED" ]]; then
      backend_args+=(--replay-speed "$REPLAY_SPEED")
    fi
  fi

  (
    cd "$ROOT_DIR"
    ./scripts/dev-backend.sh "${backend_args[@]}"
  ) >/tmp/lab-llm-audit-backend.log 2>&1 &
  backend_pid="$!"

  for _ in $(seq 1 30); do
    if health_ok; then
      break
    fi
    sleep 1
  done

  if ! health_ok; then
    echo "Failed to start dashboard backend." >&2
    echo "See /tmp/lab-llm-audit-backend.log" >&2
    exit 1
  fi
fi

if curl -fsS "$STATUS_URL" > "$status_out" 2>/dev/null; then
  :
else
  printf '{ "ingestion": null, "note": "status endpoint unavailable on audited backend" }\n' > "$status_out"
fi
curl -fsS "$SESSIONS_URL" > "$sessions_out"

if [[ -z "$PREFERRED_SESSION_ID" ]]; then
  detected_session_id="$(detect_verified_session_id)"
  if [[ -n "$detected_session_id" ]]; then
    PREFERRED_SESSION_ID="$detected_session_id"
    PREFERRED_SESSION_SOURCE="response"
  fi
fi

session_id="$(
  python - "$sessions_out" "$PREFERRED_SESSION_ID" <<'PY'
import json
import sys
from pathlib import Path

obj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
sessions = obj.get("sessions") or []
preferred = sys.argv[2]
if preferred and any(session["session_id"] == preferred for session in sessions):
    print(preferred)
else:
    running = [session for session in sessions if session.get("status") == "running"]
    if len(running) == 1:
        print(running[0]["session_id"])
    elif running:
        running.sort(key=lambda session: session.get("last_event_at") or session.get("started_at") or "", reverse=True)
        print(running[0]["session_id"])
    else:
        print(sessions[0]["session_id"] if sessions else "")
PY
)"

if [[ -n "$session_id" ]]; then
  curl -fsS "$API_BASE/api/sessions/$session_id" > "$detail_out"
else
  printf '{}' > "$detail_out"
fi

screenshot_url="$URL"
if [[ -n "$session_id" ]]; then
  screenshot_url="$(append_session_query "$URL" "$session_id")"
fi

(
  cd "$FRONTEND_DIR"
  npm run screenshot -- "$screenshot_url" "$screenshot_out"
)

{
  echo "timestamp=$timestamp"
  echo "url=$screenshot_url"
  echo "api_base=$API_BASE"
  echo "status_path=$status_out"
  echo "sessions_path=$sessions_out"
  echo "detail_path=$detail_out"
  echo "screenshot_path=$screenshot_out"
  if [[ -n "$backend_pid" ]]; then
    echo "backend_started_by_script=1"
  else
    echo "backend_started_by_script=0"
  fi
  if [[ -n "$session_id" ]]; then
    echo "session_id=$session_id"
  fi
  echo "session_selection_source=$PREFERRED_SESSION_SOURCE"
} > "$meta_out"

echo "$meta_out"
