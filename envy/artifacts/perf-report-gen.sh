#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

export ENVY_PROFILE="${ENVY_PROFILE:-balanced}"
export ENVY_CONFIG_PATH="${ENVY_CONFIG_PATH:-$ROOT_DIR/config/envy.yaml}"

python -m envy.tools.perf_report
