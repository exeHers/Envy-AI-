#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models"
CONFIG_FILE="${ROOT_DIR}/config/envy.yaml"

mkdir -p "${MODELS_DIR}"

log() {
  echo "[download-models] $*"
}

download_if_missing() {
  local url="$1"
  local target_dir="$2"
  local archive_name
  archive_name="$(basename "${url}")"
  local archive_path="${MODELS_DIR}/${archive_name}"

  if [[ -d "${target_dir}" ]]; then
    log "Model directory ${target_dir} already exists. Skipping."
    return 0
  fi

  log "Downloading ${url}"
  curl -L "${url}" -o "${archive_path}"
  log "Extracting ${archive_name}"
  unzip -q "${archive_path}" -d "${MODELS_DIR}"
  rm -f "${archive_path}"
}

log "Ensuring VOSK model is available"
download_if_missing "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" "${MODELS_DIR}/vosk-model-small-en-us-0.15"

if [[ "${1:-}" == "--with-llm" ]]; then
  LLAMA_PATH="${MODELS_DIR}/TinyLlama-1.1B-Chat-v1.0.Q4_0.gguf"
  if [[ -f "${LLAMA_PATH}" ]]; then
    log "LLM model already present at ${LLAMA_PATH}"
  else
    log "Downloading TinyLlama GGUF model"
    curl -L "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_0.gguf" -o "${LLAMA_PATH}"
  fi
else
  log "Skipping LLM model download (pass --with-llm to enable)."
fi

log "Model download routine completed."
