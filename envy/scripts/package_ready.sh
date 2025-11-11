#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="${ROOT_DIR}/packaging/envy-ready"
OUTPUT_ZIP="${ROOT_DIR}/envy-ready.zip"

rm -rf "${PACKAGE_DIR}"
mkdir -p "${PACKAGE_DIR}"

copy_items=(
  "config"
  "docs"
  "models"
  "scripts"
  "src"
  "systemd"
  "windows"
  "workspace"
  "artifacts"
  "install_envy.sh"
  "install_envy.bat"
  "run_envy_local.sh"
  "run_envy_local.bat"
  "start-envy.sh"
  "start-envy.bat"
  "Dockerfile"
  "README.md"
  "LICENSE"
  "pyproject.toml"
)

for item in "${copy_items[@]}"; do
  if [ -e "${ROOT_DIR}/${item}" ]; then
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --exclude "__pycache__" "${ROOT_DIR}/${item}" "${PACKAGE_DIR}/"
    else
      if [ -d "${ROOT_DIR}/${item}" ]; then
        cp -R "${ROOT_DIR}/${item}" "${PACKAGE_DIR}/"
      else
        cp "${ROOT_DIR}/${item}" "${PACKAGE_DIR}/"
      fi
    fi
  fi
done

pushd "${PACKAGE_DIR}" > /dev/null
zip -r "${OUTPUT_ZIP}" . > /dev/null
popd > /dev/null

rm -rf "${PACKAGE_DIR}"

echo "Created ${OUTPUT_ZIP}"
