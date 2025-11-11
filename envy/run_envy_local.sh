#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE="balanced"
DASHBOARD=true
EXTRA=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --no-gui|--no-dashboard)
      DASHBOARD=false
      shift
      ;;
    *)
      EXTRA+=("$1")
      shift
      ;;
  esac
done

ARGS=(--profile "$PROFILE" "${EXTRA[@]}")
if [[ "$DASHBOARD" == false ]]; then
  ARGS+=(--no-dashboard)
fi

exec "$SCRIPT_DIR/start-envy.sh" "${ARGS[@]}"
