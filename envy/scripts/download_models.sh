#!/bin/bash
# Download required models for Envy
# MIT License

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_ROOT/models"

echo "========================================="
echo "Envy Model Download Script"
echo "========================================="
echo ""

mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

# Download VOSK model for wake word detection
echo "[1/3] Downloading VOSK model for wake word detection..."
if [ ! -d "vosk-model-small-en-us-0.15" ]; then
    echo "Downloading VOSK model..."
    wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip -q vosk-model-small-en-us-0.15.zip
    rm vosk-model-small-en-us-0.15.zip
    echo "✓ VOSK model downloaded"
else
    echo "✓ VOSK model already exists"
fi

# Whisper models will be auto-downloaded by faster-whisper
echo ""
echo "[2/3] Whisper models will be auto-downloaded on first use"
echo "✓ Whisper setup complete"

# Download a quantized LLM model (optional)
echo ""
echo "[3/3] Downloading LLM model (optional)..."
if [ ! -f "llama-2-7b-chat.Q4_0.gguf" ]; then
    echo "Note: This is a large download (~3.8GB). Press Ctrl+C to skip."
    echo "You can also download manually from: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF"
    
    # Try to download with huggingface-cli if available
    if command -v huggingface-cli &> /dev/null; then
        echo "Downloading with huggingface-cli..."
        huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF llama-2-7b-chat.Q4_0.gguf --local-dir . --local-dir-use-symlinks False || {
            echo "⚠ Download failed. You can download manually later."
        }
    else
        echo "⚠ huggingface-cli not found. Install with: pip install huggingface-hub"
        echo "⚠ You can download the model manually and place it in $MODELS_DIR"
    fi
else
    echo "✓ LLM model already exists"
fi

echo ""
echo "========================================="
echo "Model setup complete!"
echo "========================================="
echo ""
echo "Note: If LLM model download failed, Envy will use remote API fallback."
echo "You can enable it in config/envy.yaml by setting llm.remote.enabled: true"
