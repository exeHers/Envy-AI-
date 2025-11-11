#!/bin/bash
# download_models.sh - Download required models for Envy
set -e

MODELS_DIR="${MODELS_DIR:-models}"
mkdir -p "$MODELS_DIR"

echo "Downloading models for Envy..."

# Download VOSK wake word model (small)
echo "Downloading VOSK model..."
VOSK_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
VOSK_MODEL_DIR="$MODELS_DIR/vosk-wake"

if [ ! -d "$VOSK_MODEL_DIR" ]; then
    echo "Downloading VOSK model..."
    wget -q "$VOSK_MODEL_URL" -O /tmp/vosk-model.zip
    unzip -q /tmp/vosk-model.zip -d "$MODELS_DIR"
    mv "$MODELS_DIR"/vosk-model-small-en-us-0.15 "$VOSK_MODEL_DIR"
    rm /tmp/vosk-model.zip
    echo "VOSK model downloaded"
else
    echo "VOSK model already exists"
fi

# Whisper models are downloaded automatically by the whisper library
echo "Whisper models will be downloaded automatically on first use"

# Download small LLM model (optional - user can download larger models)
echo ""
echo "For LLM, you can download quantized models from:"
echo "  - https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF"
echo "  - https://huggingface.co/models?search=gguf"
echo ""
echo "Recommended for 8GB VRAM: llama-2-7b-chat.Q4_0.gguf"
echo ""
echo "To download manually:"
echo "  wget <model-url> -O models/llama-7b-q4_0.gguf"

echo ""
echo "Model download complete!"
