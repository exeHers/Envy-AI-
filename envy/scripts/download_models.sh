#!/usr/bin/env bash
set -euo pipefail

PROFILE="balanced"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    *)
      shift 1
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHONPATH="${REPO_ROOT}" python3 "${REPO_ROOT}/scripts/download_models.py" --profile "${PROFILE}" --root "${REPO_ROOT}"
