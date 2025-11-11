#!/bin/bash
# Download required models for Envy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$BASE_DIR/models"

echo "========================================"
echo "Envy Model Downloader"
echo "========================================"

mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

# Function to download with progress
download_file() {
    local url="$1"
    local output="$2"
    
    if command -v wget &> /dev/null; then
        wget -O "$output" "$url"
    elif command -v curl &> /dev/null; then
        curl -L -o "$output" "$url"
    else
        echo "Error: Neither wget nor curl found. Please install one of them."
        exit 1
    fi
}

# Function to extract archives
extract_archive() {
    local file="$1"
    
    if [[ $file == *.zip ]]; then
        unzip -q "$file"
    elif [[ $file == *.tar.gz ]] || [[ $file == *.tgz ]]; then
        tar -xzf "$file"
    fi
}

echo ""
echo "1. Downloading VOSK wake word model..."
echo "   This is a small model (~40MB) for wake word detection."

VOSK_MODEL="vosk-model-small-en-us-0.15"
if [ ! -d "$VOSK_MODEL" ]; then
    echo "   Downloading $VOSK_MODEL..."
    download_file "https://alphacephei.com/vosk/models/$VOSK_MODEL.zip" "$VOSK_MODEL.zip"
    extract_archive "$VOSK_MODEL.zip"
    rm "$VOSK_MODEL.zip"
    echo "   ✓ VOSK model downloaded"
else
    echo "   ✓ VOSK model already exists"
fi

echo ""
echo "2. Whisper models will be auto-downloaded by faster-whisper"
echo "   on first use (models cache in ~/.cache/huggingface/)"
echo "   Default model: base (~140MB)"
echo "   You can change this in config/envy.yaml"

echo ""
echo "3. Downloading recommended LLM model (optional)..."
echo "   Model: Llama-2-7B-Chat-GGUF (Q4_K_M quantized, ~4GB)"
echo "   This may take a while depending on your connection."

read -p "   Download LLM model now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    LLM_MODEL="llama-2-7b-chat.Q4_K_M.gguf"
    if [ ! -f "$LLM_MODEL" ]; then
        echo "   Downloading $LLM_MODEL..."
        # Using TheBloke's quantized models from Hugging Face
        download_file "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/$LLM_MODEL" "$LLM_MODEL"
        echo "   ✓ LLM model downloaded"
    else
        echo "   ✓ LLM model already exists"
    fi
else
    echo "   Skipping LLM download. You can download it later."
    echo "   Note: Without LLM, Envy will use fallback responses."
fi

echo ""
echo "========================================"
echo "Model Download Complete!"
echo "========================================"
echo ""
echo "Models location: $MODELS_DIR"
echo ""
echo "Downloaded models:"
ls -lh "$MODELS_DIR"
echo ""
echo "You can now run Envy with: ./run_envy_local.sh"
echo ""
