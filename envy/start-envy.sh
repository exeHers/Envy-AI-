#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"

mkdir -p "${ARTIFACTS_DIR}"

nohup "${ROOT_DIR}/run_envy_local.sh" --profile "${1:-balanced}" --headless > "${ARTIFACTS_DIR}/envy-service.log" 2>&1 &
echo $! > "${ROOT_DIR}/artifacts/envy-service.pid"
echo "Envy service started with PID $(cat "${ROOT_DIR}/artifacts/envy-service.pid")"
