#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
LOG_FILE="${ARTIFACTS_DIR}/install-log.txt"
VENV_DIR="${ROOT_DIR}/.venv"

mkdir -p "${ARTIFACTS_DIR}"
touch "${LOG_FILE}"

PROFILE="balanced"
SKIP_LLM="false"

for arg in "$@"; do
  case "${arg}" in
    --profile=*)
      PROFILE="${arg#*=}"
      shift
      ;;
    --skip-llm)
      SKIP_LLM="true"
      shift
      ;;
    --local-demo)
      PROFILE="balanced"
      SKIP_LLM="true"
      shift
      ;;
    *)
      echo "Unknown argument: ${arg}" | tee -a "${LOG_FILE}"
      exit 1
      ;;
  esac
done

echo "[install] Starting installation at $(date -Is)" | tee -a "${LOG_FILE}"
echo "[install] Profile=${PROFILE} skip-llm=${SKIP_LLM}" | tee -a "${LOG_FILE}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "[install] Creating virtual environment." | tee -a "${LOG_FILE}"
  if ! python3 -m venv "${VENV_DIR}" >> "${LOG_FILE}" 2>&1; then
    echo "[install] python -m venv failed, falling back to virtualenv." | tee -a "${LOG_FILE}"
    python3 -m pip install --user --upgrade virtualenv >> "${LOG_FILE}" 2>&1
    python3 -m virtualenv "${VENV_DIR}" >> "${LOG_FILE}" 2>&1
  fi
fi

source "${VENV_DIR}/bin/activate"

echo "[install] Upgrading pip." | tee -a "${LOG_FILE}"
pip install --upgrade pip wheel setuptools >> "${LOG_FILE}" 2>&1

echo "[install] Installing project dependencies." | tee -a "${LOG_FILE}"
pip install -e ".[dev]" >> "${LOG_FILE}" 2>&1

if [ "${SKIP_LLM}" != "true" ]; then
  echo "[install] Downloading models (including LLM)." | tee -a "${LOG_FILE}"
  python "${ROOT_DIR}/scripts/download_models.py" >> "${LOG_FILE}" 2>&1
else
  echo "[install] Downloading audio models only." | tee -a "${LOG_FILE}"
  SKIP_LLM_DOWNLOAD=1 python "${ROOT_DIR}/scripts/download_models.py" >> "${LOG_FILE}" 2>&1 || true
fi

echo "[install] Generating default directories." | tee -a "${LOG_FILE}"
mkdir -p "${ROOT_DIR}/data" "${ARTIFACTS_DIR}/tests" "${ARTIFACTS_DIR}/logs"

cat <<EOF > "${ROOT_DIR}/envy.env"
VIRTUAL_ENV=${VENV_DIR}
PROFILE=${PROFILE}
PATH=${VENV_DIR}/bin:\$PATH
EOF

echo "[install] Installation complete." | tee -a "${LOG_FILE}"
