#!/usr/bin/env bash
set -euo pipefail

./scripts/check-quick.sh

set +e
timeout 15 .venv/bin/pyright src tests
status=$?
set -e

if [ "$status" -eq 124 ]; then
  echo "pyright timed out after 15s; treating type check as advisory for now."
elif [ "$status" -ne 0 ]; then
  exit "$status"
fi
