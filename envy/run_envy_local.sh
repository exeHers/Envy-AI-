#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PROFILE="balanced"
NO_GUI=false

usage() {
  cat <<EOF
Usage: ./run_envy_local.sh [--profile <name>] [--no-gui]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --no-gui)
      NO_GUI=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Virtual environment missing. Run ./install_envy.sh first."
  exit 1
fi

source "${VENV_DIR}/bin/activate"

CMD=("python" "-m" "envy.main" "start" "--profile" "${PROFILE}")
if [[ "${NO_GUI}" == "true" ]]; then
  CMD+=("--no-gui")
fi

exec "${CMD[@]}"
