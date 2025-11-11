#!/bin/bash
# Download required models

set -e

MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

echo "Downloading VOSK model..."
cd "$MODELS_DIR"
if [ ! -d "vosk-model-small-en-us-0.15" ]; then
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip || {
        echo "WARNING: Could not download VOSK model"
        exit 1
    }
    unzip -q vosk-model-small-en-us-0.15.zip
    rm vosk-model-small-en-us-0.15.zip
    echo "VOSK model downloaded"
else
    echo "VOSK model already exists"
fi

echo "Models ready. Whisper models will be downloaded on first use."
