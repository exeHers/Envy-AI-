from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


INCLUDE_PATHS = [
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "setup.cfg",
    "Dockerfile",
    "config/",
    "envy/",
    "skills/",
    "docs/",
    "deploy/",
    "scripts/download_models.sh",
    "scripts/download_models.ps1",
    "scripts/package_envy.py",
    "scripts/perf-report-gen.sh",
    "install_envy.sh",
    "install_envy.bat",
    "start-envy.sh",
    "start-envy.bat",
    "run_envy_local.sh",
    "run_envy_local.bat",
    "artifacts/perf-report-gen.sh",
    "models/README.md",
    "runtime/README.md",
    "tests/generate_test_audio.py",
]


def add_path(zip_file: ZipFile, root: Path, rel_path: str) -> None:
    path = root / rel_path
    if path.is_dir():
        for file in path.rglob("*"):
            if file.is_file():
                zip_file.write(file, file.relative_to(root))
    elif path.exists():
        zip_file.write(path, path.relative_to(root))


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Envy runtime into a single zip.")
    parser.add_argument("--output", default="envy-ready.zip")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output = root / args.output
    with ZipFile(output, "w", ZIP_DEFLATED) as zip_file:
        for entry in INCLUDE_PATHS:
            add_path(zip_file, root, entry)
    print(f"Packaged Envy into {output}")


if __name__ == "__main__":
    main()
