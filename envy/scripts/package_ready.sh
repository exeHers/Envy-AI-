#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/envy-ready"
OUTPUT_ZIP="${ROOT_DIR}/../envy-ready.zip"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

ROOT_DIR="${ROOT_DIR}" BUILD_DIR="${BUILD_DIR}" python3 - <<'PY'
import os
import pathlib
import shutil

root = pathlib.Path(os.environ["ROOT_DIR"])
build = pathlib.Path(os.environ["BUILD_DIR"])
include = [
    "envy",
    "config",
    "models",
    "scripts",
    "docs",
    "data",
    "artifacts",
    "README.md",
    "LICENSE",
    "Dockerfile",
    "pyproject.toml",
    "install_envy.sh",
    "install_envy.bat",
    "start-envy.sh",
    "start-envy.bat",
    "run_envy_local.sh",
    "run_envy_local.bat",
]

for item in include:
    src = root / item
    dst = build / item
    if not src.exists():
        continue
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
PY

BUILD_DIR="${BUILD_DIR}" OUTPUT_ZIP="${OUTPUT_ZIP}" python3 - <<'PY'
import os
import pathlib
import zipfile

build = pathlib.Path(os.environ["BUILD_DIR"])
zip_path = pathlib.Path(os.environ["OUTPUT_ZIP"])
if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in build.rglob("*"):
        zf.write(path, path.relative_to(build))

print(f"Created {zip_path}")
PY
