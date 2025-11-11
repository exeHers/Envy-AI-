#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
if [[ -d "${SCRIPT_DIR}/.venv" ]]; then
  VENV_DIR="${SCRIPT_DIR}/.venv"
fi

if [[ -d "${VENV_DIR}" ]]; then
  export VIRTUAL_ENV="${VENV_DIR}"
  export PATH="${VENV_DIR}/bin:${PATH}"
fi

export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

PYTHON_CMD="python"
if ! command -v "${PYTHON_CMD}" >/dev/null 2>&1; then
  PYTHON_CMD="python3"
fi

"${PYTHON_CMD}" -m envy.main "$@"
