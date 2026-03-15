#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src .venv/bin/python -m lab_llm.main "$@"
