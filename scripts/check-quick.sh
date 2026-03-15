#!/usr/bin/env bash
set -euo pipefail

.venv/bin/ruff check .
.venv/bin/pytest -q
