#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/artifacts/tests"
mkdir -p "${LOG_DIR}"

STAMP="$(date -Is | tr ':' '-')"
LOG_FILE="${LOG_DIR}/pytest-${STAMP}.log"

echo "[+] Running pytest, logging to ${LOG_FILE}"
PYTHONPATH="${REPO_ROOT}" python3 -m pytest --maxfail=1 --disable-warnings | tee "${LOG_FILE}"
