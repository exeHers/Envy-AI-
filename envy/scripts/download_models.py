#!/usr/bin/env python3
"""
Cross-platform model downloader for Envy.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Tuple

import urllib.request
import zipfile

MODELS = [
    (
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498",
        "vosk-stt",
    ),
]

LLM_MODEL: Tuple[str, str, str] = (
    "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    "c4171da4ca1198f65cf30b1f6d62075f82a0f897d1a0f446d135abfbcd7f4c6f",
    "ggml-envy-q4_0.gguf",
)


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)


def extract_zip(archive: Path, dest: Path) -> None:
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(dest)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    models_dir = root / "models"
    tmp_dir = root / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    for url, checksum, folder in MODELS:
        target_dir = models_dir / folder
        if target_dir.exists():
            print(f"[download_models.py] {folder} already present.")
            continue
        archive = tmp_dir / Path(url).name
        if not archive.exists():
            print(f"[download_models.py] Downloading {url}")
            download(url, archive)
        if sha256sum(archive) != checksum:
            print(f"[download_models.py] Checksum mismatch for {archive}, retrying download.")
            archive.unlink(missing_ok=True)
            download(url, archive)
            if sha256sum(archive) != checksum:
                raise RuntimeError(f"Checksum mismatch for {archive}")
        extract_dir = tmp_dir / f"{folder}-extract"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(exist_ok=True)
        extract_zip(archive, extract_dir)
        inner_folders = list(extract_dir.iterdir())
        if not inner_folders:
            raise RuntimeError(f"No contents extracted for {archive}")
        shutil.move(str(inner_folders[0]), target_dir)
        shutil.rmtree(extract_dir)
        print(f"[download_models.py] Extracted {folder}")

    wake_dir = models_dir / "vosk-wake"
    stt_dir = models_dir / "vosk-stt"
    if not wake_dir.exists():
        shutil.copytree(stt_dir, wake_dir)
        print("[download_models.py] Cloned STT model for wake detection.")

    if os.environ.get("SKIP_LLM_DOWNLOAD", "0") != "1":
        url, checksum, filename = LLM_MODEL
        target = models_dir / filename
        if not target.exists():
            archive = tmp_dir / filename
            if not archive.exists():
                print(f"[download_models.py] Downloading {url}")
                download(url, archive)
            if sha256sum(archive) != checksum:
                raise RuntimeError("Checksum mismatch for LLM model.")
            shutil.move(archive, target)
            print("[download_models.py] LLM model downloaded.")
    else:
        print("[download_models.py] Skipping LLM download.")


if __name__ == "__main__":
    main()
