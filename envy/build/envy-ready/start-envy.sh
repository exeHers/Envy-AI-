#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.envy-venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[start] Virtualenv not found at ${VENV_DIR}. Please run ./install_envy.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

python -m envy.core.service_launcher "$@"
