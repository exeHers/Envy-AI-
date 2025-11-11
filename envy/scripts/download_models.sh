#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models"

VOSK_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
VOSK_DIR="${MODELS_DIR}/vosk-model-small-en-us-0.15"
TINYLLAMA_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-GGUF/resolve/main/tinyllama-1.1b-chat.Q4_K_M.gguf?download=1"
TINYLLAMA_PATH="${MODELS_DIR}/tinyllama-1.1b-chat.Q4_K_M.gguf"

usage() {
  cat <<EOF
Usage: $0 [--vosk] [--tinyllama] [--all]

Downloads free, redistribution-friendly models required by Envy.
Models are stored under ${MODELS_DIR}.

Options:
  --vosk        Download Vosk small English model for wake/STT (recommended).
  --tinyllama   Download TinyLlama 1.1B chat GGUF quantized model (optional).
  --all         Download both.
EOF
  exit 1
}

mkdir -p "${MODELS_DIR}"

download_vosk() {
  if [[ -d "${VOSK_DIR}" ]]; then
    echo "[skip] Vosk model already present at ${VOSK_DIR}"
    return
  fi
  tmp_zip="$(mktemp)"
  echo "[download] Vosk model → ${tmp_zip}"
  curl -L "${VOSK_URL}" -o "${tmp_zip}"
  echo "[extract] ${tmp_zip} → ${MODELS_DIR}"
  unzip -o "${tmp_zip}" -d "${MODELS_DIR}" > /dev/null
  rm -f "${tmp_zip}"
  echo "[done] Vosk model ready at ${VOSK_DIR}"
  sha256sum "${VOSK_DIR}/README" 2>/dev/null || true
}

download_tinyllama() {
  if [[ -f "${TINYLLAMA_PATH}" ]]; then
    echo "[skip] TinyLlama already downloaded at ${TINYLLAMA_PATH}"
    return
  fi
  echo "[download] TinyLlama GGUF → ${TINYLLAMA_PATH}"
  curl -L "${TINYLLAMA_URL}" -o "${TINYLLAMA_PATH}"
  sha256sum "${TINYLLAMA_PATH}" || true
}

if [[ $# -eq 0 ]]; then
  usage
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vosk)
      download_vosk
      shift
      ;;
    --tinyllama)
      download_tinyllama
      shift
      ;;
    --all)
      download_vosk
      download_tinyllama
      shift
      ;;
    *)
      usage
      ;;
  esac
done
