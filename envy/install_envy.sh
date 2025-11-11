#!/usr/bin/env bash
set -euo pipefail

MODE="standard"
if [[ "${1:-}" == "--local-demo" ]]; then
  MODE="demo"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${REPO_ROOT}/artifacts"
LOG_FILE="${LOG_DIR}/install-log.txt"
VENV_DIR="${REPO_ROOT}/.venv"

mkdir -p "${LOG_DIR}"
echo "=== Envy installer started ($(date -Is)) ===" | tee "${LOG_FILE}"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[1/6] Creating Python virtual environment at ${VENV_DIR}"
if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"

echo "[2/6] Upgrading pip"
pip install --upgrade pip

echo "[3/6] Installing Envy package dependencies"
pip install -e "${REPO_ROOT}[dev]"

echo "[4/6] Downloading acoustic/LLM models (mode=${MODE})"
PROFILE="balanced"
if [[ "${MODE}" == "demo" ]]; then
  PROFILE="low"
fi
"${REPO_ROOT}/scripts/download_models.sh" --profile "${PROFILE}"

echo "[5/6] Preparing runtime directories"
mkdir -p "${REPO_ROOT}/artifacts/tests"
mkdir -p "${REPO_ROOT}/artifacts/logs"
mkdir -p "${REPO_ROOT}/workspace"

echo "[6/6] Installer finished successfully."

cat <<EOF
Next steps:
  source "${VENV_DIR}/bin/activate"
  python -m envy.cli run --audio-file tests/data/wake_command.wav --profile ${PROFILE}
EOF
