from __future__ import annotations

import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from envy.services.common.config import load_config, PROJECT_ROOT


def iter_files(path: Path):
    if path.is_file():
        yield path, path.name
    else:
        for root, _, files in os.walk(path):
            root_path = Path(root)
            for name in files:
                file_path = root_path / name
                rel = file_path.relative_to(PROJECT_ROOT)
                yield file_path, rel


def create_package() -> Path:
    config = load_config()
    output_name = config.get("packaging.output_zip", "envy-ready.zip")
    output_path = PROJECT_ROOT / output_name

    include_dirs = config.get("packaging.include_dirs", [])
    include_files = config.get("packaging.include_files", [])

    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        for directory in include_dirs:
            dir_path = (PROJECT_ROOT / directory).resolve()
            if not dir_path.exists():
                continue
            for file_path, rel in iter_files(dir_path):
                archive.write(file_path, rel.as_posix())
        for file_entry in include_files:
            file_path = (PROJECT_ROOT / file_entry).resolve()
            if file_path.exists():
                archive.write(file_path, file_entry)

    return output_path


def main() -> None:
    path = create_package()
    print(f"[package] Created {path}")


if __name__ == "__main__":
    main()
