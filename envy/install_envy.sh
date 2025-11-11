#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
LOG_FILE="${ARTIFACTS_DIR}/install-log.txt"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON:-python3}"
MODELS_MODE="minimal"

mkdir -p "${ARTIFACTS_DIR}"
touch "${LOG_FILE}"

exec > >(tee -a "${LOG_FILE}") 2>&1
echo "[$(date --iso-8601=seconds)] Starting Envy installation..."

for arg in "$@"; do
  case "$arg" in
    --local-demo)
      MODELS_MODE="minimal"
      ;;
    --full-models)
      MODELS_MODE="full"
      ;;
    *)
      echo "Unknown argument: ${arg}"
      ;;
  esac
done

# shellcheck disable=SC1091
create_venv() {
  if [ -d "${VENV_DIR}" ]; then
    if [ -f "${VENV_DIR}/bin/activate" ]; then
      return
    fi
    echo "Existing virtual environment missing activation script; recreating..."
    rm -rf "${VENV_DIR}"
  fi

  echo "Creating virtual environment at ${VENV_DIR}"
  if "${PYTHON_BIN}" -m venv "${VENV_DIR}" 2>/dev/null; then
    if [ -f "${VENV_DIR}/bin/activate" ]; then
      return
    fi
    echo "venv created but activate script missing; retrying with virtualenv..."
    rm -rf "${VENV_DIR}"
  fi

  echo "Standard venv failed; falling back to virtualenv bootstrap..."
  "${PYTHON_BIN}" -m pip install --upgrade virtualenv
  "${PYTHON_BIN}" -m virtualenv "${VENV_DIR}"
}

create_venv

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip wheel
python -m pip install ".[tests]"

echo "Preparing local models (mode=${MODELS_MODE})"
bash "${ROOT_DIR}/scripts/download_models.sh" "--${MODELS_MODE}"

echo "[$(date --iso-8601=seconds)] Installation complete."
