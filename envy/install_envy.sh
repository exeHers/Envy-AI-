#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/artifacts"
LOG_FILE="$LOG_DIR/install-log.txt"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="${PYTHON:-python3}"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[install] Starting Envy installation at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

for tool in curl unzip; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "[install] Missing dependency: $tool. Please install it and re-run."
    exit 1
  fi
done

DOWNLOAD_ARGS=()
SKIP_DOWNLOADS=false

for arg in "$@"; do
  case "$arg" in
    --local-demo)
      DOWNLOAD_ARGS+=(--demo)
      ;;
    --full-models)
      DOWNLOAD_ARGS+=(--full)
      ;;
    --skip-model-download)
      SKIP_DOWNLOADS=true
      ;;
    *)
      echo "[install] Unknown option: $arg"
      exit 1
      ;;
  esac
done

if [[ ! -d "$VENV_DIR" ]]; then
  echo "[install] Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "[install] Activating virtual environment"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

echo "[install] Upgrading pip"
pip install --upgrade pip wheel

echo "[install] Installing Envy dependencies"
pip install -e ".[dev]"

if [[ "$SKIP_DOWNLOADS" == false ]]; then
  if [[ "${#DOWNLOAD_ARGS[@]}" -eq 0 ]]; then
    DOWNLOAD_ARGS=(--demo)
  fi
  echo "[install] Downloading models with args: ${DOWNLOAD_ARGS[*]}"
  "$SCRIPT_DIR/scripts/download_models.sh" "${DOWNLOAD_ARGS[@]}"
else
  echo "[install] Skipping model downloads as requested."
fi

echo "[install] Installation completed successfully."
echo "[install] Virtual environment: $VENV_DIR"
echo "[install] To start Envy, run: ./start-envy.sh --dashboard"
