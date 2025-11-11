#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Virtual environment not found. Run ./install_envy.sh first."
  exit 1
fi

source "${VENV_DIR}/bin/activate"

PROFILE="balanced"
HEADLESS="false"
GUI="true"

while (( "$#" )); do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --no-gui)
      HEADLESS="true"
      shift
      ;;
    --headless)
      HEADLESS="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

python -m envy.cli start --profile "${PROFILE}" $( [ "${HEADLESS}" == "true" ] && echo "--headless" )
