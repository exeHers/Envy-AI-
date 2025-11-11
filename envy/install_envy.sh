#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
LOG_FILE="${ARTIFACTS_DIR}/install-log.txt"
VENV_DIR="${ROOT_DIR}/.envy-venv"
PROFILE="balanced"
REGISTER_SYSTEMD=false

usage() {
  cat <<EOF
Usage: ./install_envy.sh [options]

Options:
  --venv PATH           Path to virtual environment (default: ${VENV_DIR})
  --profile NAME        Runtime profile to preset (default: balanced)
  --register-systemd    Attempt to install the systemd unit (requires sudo)
  --llm                 Also download optional local LLM model
  --force-models        Force re-download of models
  --help                Show this help message
EOF
}

DOWNLOAD_LLM=false
FORCE_MODELS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv)
      VENV_DIR="$2"
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --register-systemd)
      REGISTER_SYSTEMD=true
      shift
      ;;
    --llm)
      DOWNLOAD_LLM=true
      shift
      ;;
    --force-models)
      FORCE_MODELS=true
      shift
      ;;
    --local-demo)
      # Alias for default behaviour (no optional downloads)
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

mkdir -p "${ARTIFACTS_DIR}"
timestamp="$(date --iso-8601=seconds)"
echo "[install] Starting at ${timestamp}" | tee "${LOG_FILE}"

create_venv() {
  if python3 -m venv "${VENV_DIR}" >/dev/null 2>&1; then
    return 0
  fi
  echo "[install] python3-venv missing; installing virtualenv fallback..."
  python3 -m pip install --user virtualenv
  python3 -m virtualenv "${VENV_DIR}"
}

create_venv
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip build wheel
python -m pip install "${ROOT_DIR}[dev]"

MODEL_FLAGS=()
[[ "${DOWNLOAD_LLM}" == true ]] && MODEL_FLAGS+=("--llm")
[[ "${FORCE_MODELS}" == true ]] && MODEL_FLAGS+=("--force")
bash "${ROOT_DIR}/scripts/download_models.sh" "${MODEL_FLAGS[@]}"

CONFIG_FILE="${ROOT_DIR}/config/envy.yaml"
if [[ -f "${CONFIG_FILE}" ]]; then
  python - <<PY
import yaml
from pathlib import Path

config_path = Path("${CONFIG_FILE}")
data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
data["active_profile"] = "${PROFILE}"
config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY
fi

if [[ "${REGISTER_SYSTEMD}" == true ]]; then
  UNIT_SRC="${ROOT_DIR}/installers/systemd/envy.service"
  if [[ -f "${UNIT_SRC}" ]]; then
    echo "[install] Attempting to install systemd unit..."
    sudo cp "${UNIT_SRC}" /etc/systemd/system/envy.service
    sudo systemctl daemon-reload
    sudo systemctl enable envy.service
    echo "[install] systemd unit installed (not started automatically)."
  else
    echo "[install] systemd unit template missing at ${UNIT_SRC}" >&2
  fi
fi

echo "[install] Installation complete. Virtualenv: ${VENV_DIR}"
echo "[install] $(date --iso-8601=seconds)" >> "${LOG_FILE}"
