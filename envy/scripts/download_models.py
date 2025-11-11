from __future__ import annotations

import argparse
import pathlib
import urllib.request
import zipfile


def fetch(url: str, target: pathlib.Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"[+] Fetching {url} -> {target}")
    urllib.request.urlretrieve(url, target)
    print("[+] Download complete")


def ensure_vosk(models_dir: pathlib.Path) -> None:
    marker = models_dir / "vosk-model-small-en-us-0.15"
    if marker.exists():
        print("[+] Vosk model already present.")
        return
    zip_path = models_dir / "vosk-model-small-en-us-0.15.zip"
    fetch(
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        zip_path,
    )
    print("[+] Extracting Vosk model...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(models_dir)
    zip_path.unlink()
    print("[+] Vosk model ready.")


def ensure_whisper(models_dir: pathlib.Path) -> None:
    target = models_dir / "ggml-small.bin"
    if target.exists():
        print("[+] Whisper model already present.")
        return
    fetch(
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
        target,
    )


def ensure_llm(models_dir: pathlib.Path) -> None:
    target = models_dir / "llama-3-8b-instruct-q4_k_m.gguf"
    if target.exists():
        print("[+] GGUF model already present.")
        return
    fetch(
        "https://huggingface.co/Hubert-Wu/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf?download=true",
        target,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="balanced", choices=["low", "balanced", "power"])
    parser.add_argument("--root", default=".", help="Repository root path")
    args = parser.parse_args()

    repo_root = pathlib.Path(args.root).resolve()
    models_dir = repo_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    ensure_vosk(models_dir / "vosk")
    if args.profile == "power":
        ensure_whisper(models_dir / "whisper")
        ensure_llm(models_dir / "llm")

    print(f"[+] Model preparation complete for profile {args.profile}.")


if __name__ == "__main__":
    main()
