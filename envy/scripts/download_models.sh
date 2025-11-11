#!/bin/bash
# Download models for Envy
# This script downloads free, lightweight models for local inference

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="$BASE_DIR/models"

echo "=== Envy Model Downloader ==="
echo "Base directory: $BASE_DIR"
echo "Model directory: $MODEL_DIR"
echo ""

# Create model directory
mkdir -p "$MODEL_DIR"

# Function to download with progress
download_file() {
    local url="$1"
    local output="$2"
    echo "Downloading: $output"
    if command -v wget &> /dev/null; then
        wget -q --show-progress -O "$output" "$url"
    elif command -v curl &> /dev/null; then
        curl -L --progress-bar -o "$output" "$url"
    else
        echo "Error: Neither wget nor curl found. Please install one of them."
        exit 1
    fi
}

# Download VOSK models for wake word and STT
echo "1. Downloading VOSK models..."
echo ""

# Small model for wake word (lightweight)
if [ ! -d "$MODEL_DIR/vosk-model-small-en-us-0.15" ]; then
    echo "Downloading VOSK small model for wake word detection..."
    cd "$MODEL_DIR"
    download_file "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" "vosk-small.zip"
    echo "Extracting..."
    unzip -q vosk-small.zip
    rm vosk-small.zip
    echo "✓ VOSK small model installed"
else
    echo "✓ VOSK small model already exists"
fi

# Medium model for STT (better accuracy)
if [ ! -d "$MODEL_DIR/vosk-model-en-us-0.22" ]; then
    echo ""
    echo "Downloading VOSK medium model for speech recognition..."
    cd "$MODEL_DIR"
    download_file "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip" "vosk-medium.zip"
    echo "Extracting..."
    unzip -q vosk-medium.zip
    rm vosk-medium.zip
    echo "✓ VOSK medium model installed"
else
    echo "✓ VOSK medium model already exists"
fi

# Download TinyLlama for local LLM
echo ""
echo "2. Downloading TinyLlama model for local AI..."
echo ""

if [ ! -f "$MODEL_DIR/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo "Downloading TinyLlama (quantized, ~700MB)..."
    cd "$MODEL_DIR"
    download_file "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    echo "✓ TinyLlama model installed"
else
    echo "✓ TinyLlama model already exists"
fi

# Create model info file
echo ""
echo "3. Creating model info..."
cat > "$MODEL_DIR/README.md" << 'EOF'
# Envy Models

This directory contains the models used by Envy Personal Assistant.

## Installed Models

### VOSK Models (Speech Recognition)
- **vosk-model-small-en-us-0.15**: Lightweight model for wake word detection (~40MB)
- **vosk-model-en-us-0.22**: Medium model for speech-to-text (~1.8GB)
- License: Apache 2.0
- Source: https://alphacephei.com/vosk/models

### TinyLlama (Language Model)
- **tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf**: Quantized language model (~700MB)
- Context: 2048 tokens
- License: Apache 2.0
- Source: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF

## Upgrading Models

For better performance (requires more resources):

### Better STT:
- vosk-model-en-us-0.42-gigaspeech (2.4GB)
- Or use Whisper models via openai-whisper

### Better LLM:
- Llama-2-7B-Chat-GGUF (Q4_K_M, ~4GB)
- Mistral-7B-Instruct-GGUF (Q4_K_M, ~4GB)

Download from HuggingFace and update paths in config/envy.yaml
EOF

echo "✓ Model info created"
echo ""
echo "=== Model Download Complete ==="
echo ""
echo "Installed models:"
ls -lh "$MODEL_DIR" | grep -E '(vosk|tinyllama|\.gguf)'
echo ""
echo "Total size:"
du -sh "$MODEL_DIR"
echo ""
echo "Models are ready to use!"
