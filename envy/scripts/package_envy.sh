#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${REPO_ROOT}/../envy-ready.zip"

echo "[+] Packaging Envy into ${OUTPUT}"
rm -f "${OUTPUT}"

INCLUDE=(
  "README.md"
  "LICENSE"
  "pyproject.toml"
  "config/"
  "docs/"
  "envy/"
  "scripts/"
  "templates/"
  "static/"
  "tests/data/wake_command.wav"
  "install_envy.sh"
  "install_envy.bat"
  "run_envy_local.sh"
  "run_envy_local.bat"
  "start-envy.sh"
  "start-envy.bat"
  "deploy/"
  "artifacts/perf-report-gen.sh"
  "models/README.md"
)

PYTHONPATH="${REPO_ROOT}" python3 - <<'PY' "$REPO_ROOT" "$OUTPUT" "${INCLUDE[@]}"
import sys
import pathlib
import zipfile

repo = pathlib.Path(sys.argv[1])
output = pathlib.Path(sys.argv[2])
targets = sys.argv[3:]

with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for rel in targets:
        path = repo / rel
        if not path.exists():
            continue
        if path.is_dir():
            for file in path.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(repo))
        else:
            zf.write(path, path.relative_to(repo))

print(f"[+] Created archive at {output}")
PY
