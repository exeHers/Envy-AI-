#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="balanced"
NO_GUI=false

usage() {
  cat <<EOF
Usage: ./run_envy_local.sh [options]

Options:
  --profile NAME   Runtime profile (low|balanced|power) [default: balanced]
  --no-gui         Skip starting the web dashboard
  --help           Show this help message
EOF
}

ARGS=()
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
      ARGS+=("$1")
      shift
      ;;
  esac
done

CMD_ARGS=(--profile "${PROFILE}" --config "${ROOT_DIR}/config/envy.yaml")
if [[ "${NO_GUI}" == true ]]; then
  CMD_ARGS+=(--no-dashboard)
fi

exec "${ROOT_DIR}/start-envy.sh" "${CMD_ARGS[@]}" "${ARGS[@]}"
