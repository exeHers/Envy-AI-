#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DOWNLOAD_DIR="$ROOT_DIR/downloads"
MODEL_DIR="$ROOT_DIR/models"

DOWNLOAD_MODE="demo"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--demo] [--full] [--skip-llm]

--demo       Download only lightweight models required for automated tests (default).
--full       Download recommended Vosk + optional llama.cpp model (larger).
--skip-llm   Skip optional local LLM download even in full mode.
EOF
}

SKIP_LLM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --demo)
      DOWNLOAD_MODE="demo"
      shift
      ;;
    --full)
      DOWNLOAD_MODE="full"
      shift
      ;;
    --skip-llm)
      SKIP_LLM=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

mkdir -p "$DOWNLOAD_DIR" "$MODEL_DIR"

download_and_unpack() {
  local url="$1"
  local archive_name="$2"
  local target_dir="$3"

  local archive_path="$DOWNLOAD_DIR/$archive_name"
  if [[ ! -f "$archive_path" ]]; then
    echo "[models] Downloading $archive_name"
    curl -L "$url" -o "$archive_path"
  else
    echo "[models] Using cached $archive_name"
  fi

  if [[ "$archive_name" == *.zip ]]; then
    unzip -o "$archive_path" -d "$MODEL_DIR"
  else
    tar -xf "$archive_path" -C "$MODEL_DIR"
  fi
}

ensure_vosk() {
  local model_tag="vosk-model-small-en-us-0.15"
  local target="$MODEL_DIR/$model_tag"
  if [[ -d "$target" ]]; then
    echo "[models] Vosk model already present at $target"
    return
  fi
  download_and_unpack \
    "https://alphacephei.com/vosk/models/$model_tag.zip" \
    "$model_tag.zip" \
    "$target"
}

ensure_demo_assets() {
  ensure_vosk
  mkdir -p "$MODEL_DIR/llama"
  if [[ ! -f "$MODEL_DIR/llama/README.md" ]]; then
    cat <<'EOF' > "$MODEL_DIR/llama/README.md"
Local LLM placeholder.

The default Envy configuration uses a rule-based fallback. To enable local LLM
support, run:

  scripts/download_models.sh --full

and enable `llm.llama_cpp.enabled` in `config/envy.yaml` once the model is in place.
EOF
  fi
}

ensure_llama() {
  local llama_tag="ggml-alpaca-7b-q4.bin"
  local target="$MODEL_DIR/llama/$llama_tag"
  if [[ -f "$target" ]]; then
    echo "[models] llama.cpp model already present."
    return
  fi
  mkdir -p "$MODEL_DIR/llama"
  echo "[models] Downloading optional llama.cpp model (~4GB)."
  echo "Press Ctrl+C to abort if this is not desired."
  sleep 3
  curl -L "https://huggingface.co/ggml-org/ggml-alpaca-7b-q4/resolve/main/$llama_tag" -o "$target"
}

if [[ "$DOWNLOAD_MODE" == "demo" ]]; then
  ensure_demo_assets
else
  ensure_vosk
  ensure_demo_assets
  if [[ "$SKIP_LLM" == false ]]; then
    ensure_llama
  else
    echo "[models] Skipping llama.cpp model download."
  fi
fi

echo "[models] Downloads complete."
