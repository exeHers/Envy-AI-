#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
OUT_FILE="${ROOT_DIR}/artifacts/perf-report.txt"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Virtual environment missing. Run install_envy.sh first."
  exit 1
fi

source "${VENV_DIR}/bin/activate"

python "${ROOT_DIR}/scripts/perf_report.py" > "${OUT_FILE}"
echo "Performance report saved to ${OUT_FILE}"
