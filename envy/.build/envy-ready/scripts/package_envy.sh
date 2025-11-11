#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_ZIP="${ROOT_DIR}/envy-ready.zip"
TEMP_DIR="${ROOT_DIR}/.build/envy-ready"

rm -rf "${ROOT_DIR}/.build"
mkdir -p "${TEMP_DIR}"

copy_paths=(
  "install_envy.sh"
  "install_envy.bat"
  "run_envy_local.sh"
  "run_envy_windows.bat"
  "start-envy.sh"
  "start-envy.bat"
  "config"
  "services"
  "skills"
  "scripts"
  "data/audio_samples"
  "packaging"
  "artifacts/perf-report-gen.sh"
  "LICENSE"
  "README.md"
  "docs"
)

for item in "${copy_paths[@]}"; do
  if [[ -e "${ROOT_DIR}/${item}" ]]; then
    mkdir -p "$(dirname "${TEMP_DIR}/${item}")"
    cp -R "${ROOT_DIR}/${item}" "${TEMP_DIR}/${item}"
  fi
done

if [[ -d "${ROOT_DIR}/models/vosk-model-small-en-us-0.15" ]]; then
  mkdir -p "${TEMP_DIR}/models"
  cp -R "${ROOT_DIR}/models/vosk-model-small-en-us-0.15" "${TEMP_DIR}/models/"
fi

mkdir -p "${TEMP_DIR}/artifacts"
touch "${TEMP_DIR}/artifacts/.placeholder"

rm -f "${OUTPUT_ZIP}"
(
  cd "${TEMP_DIR}/.."
  zip -r "${OUTPUT_ZIP}" "envy-ready" >/dev/null
)

echo "Packaged ${OUTPUT_ZIP}"
