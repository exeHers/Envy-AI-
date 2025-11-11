#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/envy-ready"
OUTPUT_ZIP="${ROOT_DIR}/envy-ready.zip"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

copy_paths=(
  "README.md"
  "LICENSE"
  "pyproject.toml"
  "config"
  "skills"
  "scripts"
  "docs"
  "assets/audio"
  "install_envy.sh"
  "install_envy.bat"
  "start-envy.sh"
  "start-envy.bat"
  "run_envy_local.sh"
  "run_envy_local.bat"
  "envy"
  "installers"
)

for path in "${copy_paths[@]}"; do
  src="${ROOT_DIR}/${path}"
  if [[ -e "${src}" ]]; then
    cp -a "${src}" "${BUILD_DIR}/"
  fi
done

# Include small models if present (e.g., Vosk) but skip large optional downloads.
if [[ -d "${ROOT_DIR}/artifacts/models/vosk-model-small-en-us-0.15" ]]; then
  mkdir -p "${BUILD_DIR}/artifacts/models"
  cp -a "${ROOT_DIR}/artifacts/models/vosk-model-small-en-us-0.15" "${BUILD_DIR}/artifacts/models/"
else
  mkdir -p "${BUILD_DIR}/artifacts"
fi

# Ensure artifacts/tests/ exists
mkdir -p "${BUILD_DIR}/artifacts/tests"

(
  cd "${BUILD_DIR}/.."
  zip -rq "${OUTPUT_ZIP}" "envy-ready"
)

echo "[package] Created ${OUTPUT_ZIP}"
