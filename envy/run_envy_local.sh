#!/usr/bin/env bash
set -euo pipefail

PROFILE="balanced"
DASHBOARD="false"
AUDIO_FILE=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --audio-file)
      AUDIO_FILE="$2"
      shift 2
      ;;
    --dashboard)
      DASHBOARD="true"
      shift 1
      ;;
    --no-dashboard)
      DASHBOARD="false"
      shift 1
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift 1
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Virtual environment not found. Run ./install_envy.sh first."
  exit 1
fi

source "${VENV_DIR}/bin/activate"

CMD=(python -m envy.cli run --profile "${PROFILE}")
if [[ "${DASHBOARD}" == "true" ]]; then
  CMD+=(--dashboard)
fi
if [[ -n "${AUDIO_FILE}" ]]; then
  CMD+=(--audio-file "${AUDIO_FILE}")
fi
CMD+=("${EXTRA_ARGS[@]}")

echo "Executing: ${CMD[*]}"
PYTHONPATH="${REPO_ROOT}" "${CMD[@]}"
