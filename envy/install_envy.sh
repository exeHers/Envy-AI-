#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${ROOT_DIR}/artifacts/install-log.txt"
VENV_DIR="${ROOT_DIR}/.venv"

touch "${LOG_FILE}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[install] Envy installation started at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[error] python3 not found in PATH."
  exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
echo "[info] Using python ${PYTHON_VERSION}"

create_venv() {
  if python3 -m venv "${VENV_DIR}" 2>/dev/null; then
    return 0
  fi
  echo "[warn] python3 -m venv unavailable. Installing virtualenv fallback..."
  if ! python3 -m pip install --user --upgrade virtualenv; then
    echo "[error] Failed to install virtualenv. Install python3-venv or virtualenv manually."
    return 1
  fi
  if python3 -m virtualenv "${VENV_DIR}"; then
    return 0
  fi
  echo "[error] Could not create a virtual environment. Install python3-venv."
  return 1
}

if [[ -d "${VENV_DIR}" && ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "[warn] Existing virtual environment is incomplete. Recreating..."
  rm -rf "${VENV_DIR}"
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[setup] Creating virtual environment at ${VENV_DIR}"
  if ! create_venv; then
    exit 1
  fi
fi

source "${VENV_DIR}/bin/activate"
pip install --upgrade pip wheel
pip install -e "${ROOT_DIR}"

echo "[models] Downloading Vosk wake/STT model"
bash "${ROOT_DIR}/scripts/download_models.sh" --vosk

echo "[audio] Pre-generating demo audio samples"
python "${ROOT_DIR}/tests/generate_test_audio.py"

SYSTEMD_UNIT_TEMPLATE="${ROOT_DIR}/deploy/systemd/envy.service"
SYSTEMD_OUTPUT="${ROOT_DIR}/deploy/systemd/envy.generated.service"
if [[ -f "${SYSTEMD_UNIT_TEMPLATE}" ]]; then
  sed \
    -e "s|{{ENVY_HOME}}|${ROOT_DIR}|g" \
    -e "s|{{ENVY_VENV}}|${VENV_DIR}|g" \
    "${SYSTEMD_UNIT_TEMPLATE}" > "${SYSTEMD_OUTPUT}"
  echo "[systemd] Generated unit template at ${SYSTEMD_OUTPUT}"
fi

echo "[install] Completed successfully at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "[install] Activate with: source ${VENV_DIR}/bin/activate && ./start-envy.sh --profile balanced"
