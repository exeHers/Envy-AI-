#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
ARTIFACTS_TESTS="${ROOT_DIR}/artifacts/tests"
LOG_FILE="${ARTIFACTS_TESTS}/pytest.log"

mkdir -p "${ARTIFACTS_TESTS}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Virtual environment missing. Run install_envy.sh first." | tee "${LOG_FILE}"
  exit 1
fi

source "${VENV_DIR}/bin/activate"

pytest "${ROOT_DIR}/tests" --maxfail=1 --disable-warnings -q | tee "${LOG_FILE}"
