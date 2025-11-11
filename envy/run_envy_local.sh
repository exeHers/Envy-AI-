#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE="balanced"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --no-gui)
      EXTRA_ARGS+=("--no-dashboard")
      shift
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

exec "${SCRIPT_DIR}/start-envy.sh" --profile "${PROFILE}" "${EXTRA_ARGS[@]}"
