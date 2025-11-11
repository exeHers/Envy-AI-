#!/usr/bin/env python3
"""Cross-platform model downloader for Envy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT_DIR / "artifacts" / "models"

VOSK_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
VOSK_SHA256 = "30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498"

LLM_URL = "https://huggingface.co/lmstudio-community/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf"
LLM_SHA256 = "f8d41a136f89b5d142bb1d3c079ec31a0f65379b3f10d1f4a7a2325405cb9189"


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as response, dest.open("wb") as out:
        total = int(response.headers.get("Content-Length", 0))
        read = 0
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out.write(chunk)
            read += len(chunk)
            if total:
                percent = read / total * 100
                print(f"\r[download] {dest.name}: {percent:.1f}% ({read}/{total})", end="")
        print()


def ensure_vosk(force: bool) -> None:
    target_dir = MODELS_DIR / "vosk-model-small-en-us-0.15"
    if target_dir.exists() and not force:
        print("[models] Vosk model already present.")
        return
    zip_path = MODELS_DIR / "vosk-model-small-en-us-0.15.zip"
    download(VOSK_URL, zip_path)
    checksum = sha256sum(zip_path)
    if checksum != VOSK_SHA256:
        raise RuntimeError(f"Checksum mismatch for {zip_path}: {checksum}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(MODELS_DIR)
    zip_path.unlink()
    print("[models] Vosk model ready.")


def ensure_llm(force: bool) -> None:
    target_path = MODELS_DIR / "tinyllama-1.1b-chat.gguf"
    if target_path.exists() and not force:
        print("[models] TinyLlama already present.")
        return
    download(LLM_URL, target_path)
    checksum = sha256sum(target_path)
    if checksum != LLM_SHA256:
        raise RuntimeError(f"Checksum mismatch for {target_path}: {checksum}")
    print("[models] TinyLlama model ready.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download models for Envy.")
    parser.add_argument("--llm", action="store_true", help="Download optional TinyLlama GGUF model")
    parser.add_argument("--force", action="store_true", help="Force re-download even if files exist")
    args = parser.parse_args(argv)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ensure_vosk(args.force)
    if args.llm:
        ensure_llm(args.force)
    else:
        print("[models] Skipping optional TinyLlama download (use --llm).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
