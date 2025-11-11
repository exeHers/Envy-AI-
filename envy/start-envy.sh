#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"

if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

ENVY_PROFILE="${ENVY_PROFILE:-balanced}"
ENVY_CONFIG_PATH="${ENVY_CONFIG_PATH:-$SCRIPT_DIR/config/envy.yaml}"
export ENVY_PROFILE ENVY_CONFIG_PATH

exec python -m envy.scripts.process_manager start --profile "$ENVY_PROFILE" --config "$ENVY_CONFIG_PATH" "$@"
