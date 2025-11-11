#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEFAULT_PROFILE="balanced"
ARGS=("$@")
if [[ $# -eq 0 ]]; then
  ARGS=(--profile "${DEFAULT_PROFILE}")
fi

"${SCRIPT_DIR}/start-envy.sh" "${ARGS[@]}"
