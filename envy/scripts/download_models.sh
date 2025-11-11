#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models"
TMP_DIR="${ROOT_DIR}/.tmp"

mkdir -p "${MODELS_DIR}" "${TMP_DIR}"

download_and_extract() {
  local url="$1"
  local sha="$2"
  local dest_dir="$3"
  local archive="${TMP_DIR}/$(basename "${url}")"

  if [ -d "${dest_dir}" ]; then
    echo "[download_models] ${dest_dir} already present; skipping."
    return
  fi

  if [ ! -f "${archive}" ]; then
    echo "[download_models] Fetching ${url}"
    curl -L "${url}" -o "${archive}"
  else
    echo "[download_models] Using cached ${archive}"
  fi

  echo "${sha}  ${archive}" | sha256sum --check --status || {
    echo "Checksum mismatch for ${archive}" >&2
    exit 1
  }

  mkdir -p "${dest_dir}"
  case "${archive}" in
    *.zip)
      unzip -q "${archive}" -d "${TMP_DIR}"
      local inner_dir
      inner_dir="$(find "${TMP_DIR}" -maxdepth 1 -mindepth 1 -type d | head -n 1)"
      mv "${inner_dir}" "${dest_dir}"
      ;;
    *.tar.gz|*.tgz)
      tar -xzf "${archive}" -C "${dest_dir}" --strip-components=1
      ;;
    *)
      echo "Unsupported archive format: ${archive}" >&2
      exit 1
      ;;
  esac
}

download_llama() {
  local url="$1"
  local sha="$2"
  local dest="${MODELS_DIR}/ggml-envy-q4_0.gguf"
  if [ -f "${dest}" ]; then
    echo "[download_models] LLM already present."
    return
  fi
  local archive="${TMP_DIR}/$(basename "${url}")"
  if [ ! -f "${archive}" ]; then
    echo "[download_models] Downloading ${url}"
    curl -L "${url}" -o "${archive}"
  fi
  echo "${sha}  ${archive}" | sha256sum --check --status || {
    echo "Checksum mismatch for LLM archive" >&2
    exit 1
  }
  mv "${archive}" "${dest}"
  echo "[download_models] Saved ${dest}"
}

# VOSK models
download_and_extract \
  "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" \
  "30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498" \
  "${MODELS_DIR}/vosk-stt"

# Use same model for wake detection (keyword spotting)
if [ ! -d "${MODELS_DIR}/vosk-wake" ]; then
  cp -r "${MODELS_DIR}/vosk-stt" "${MODELS_DIR}/vosk-wake"
fi

if [ "${SKIP_LLM_DOWNLOAD:-0}" != "1" ]; then
  download_llama \
    "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
    "c4171da4ca1198f65cf30b1f6d62075f82a0f897d1a0f446d135abfbcd7f4c6f"
else
  echo "[download_models] SKIP_LLM_DOWNLOAD=1, skipping LLM download."
fi

echo "[download_models] Models ready in ${MODELS_DIR}"
