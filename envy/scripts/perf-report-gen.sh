#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -d "${ROOT_DIR}/.envy-venv" ]]; then
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.envy-venv/bin/activate"
fi

python "${ROOT_DIR}/scripts/perf_report.py" "$@"
