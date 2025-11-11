#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${SCRIPT_DIR}/artifacts/perf-report.txt"

export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

PYTHON_CMD="python"
if ! command -v "${PYTHON_CMD}" >/dev/null 2>&1; then
  PYTHON_CMD="python3"
fi

"${PYTHON_CMD}" -m envy.tools.perf_report --output "${OUTPUT}"
