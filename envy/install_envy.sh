#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
LOG_FILE="${ARTIFACTS_DIR}/install-log.txt"
VENV_DIR="${ROOT_DIR}/.venv"

mkdir -p "${ARTIFACTS_DIR}"
exec > >(tee "${LOG_FILE}") 2>&1

usage() {
  cat <<EOF
Usage: ./install_envy.sh [--local-demo] [--with-llm]

Options:
  --local-demo    Install minimal dependencies and skip service registration.
  --with-llm      Download the optional TinyLlama GGUF model (~600MB).
EOF
}

LOCAL_DEMO=false
WITH_LLM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local-demo) LOCAL_DEMO=true ;;
    --with-llm) WITH_LLM=true ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
  shift
done

echo "[install] Starting Envy installation at $(date)"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install ".[dev]"

echo "[install] Downloading models"
if [[ "${WITH_LLM}" == "true" ]]; then
  bash "${ROOT_DIR}/scripts/download_models.sh" --with-llm
else
  bash "${ROOT_DIR}/scripts/download_models.sh"
fi

if [[ "${LOCAL_DEMO}" == "true" ]]; then
  echo "[install] Local demo mode selected; skipping service registration."
else
  echo "[install] Skipping service registration (not implemented in demo environment)."
fi

echo "[install] Installation complete."
