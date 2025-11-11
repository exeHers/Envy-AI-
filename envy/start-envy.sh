#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "${REPO_ROOT}/run_envy_local.sh" --no-dashboard "$@"
