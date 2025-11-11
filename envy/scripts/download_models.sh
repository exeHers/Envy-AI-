#!/bin/bash
# Download models script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

mkdir -p models
cd models

echo "Downloading VOSK model..."
if [ ! -d "vosk-model-small-en-us-0.15" ]; then
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip -q vosk-model-small-en-us-0.15.zip
    rm vosk-model-small-en-us-0.15.zip
    echo "VOSK model downloaded"
else
    echo "VOSK model already present"
fi

echo ""
echo "Optional: Download local LLM model"
echo "For local LLM support, download a GGUF model:"
echo "  Example: llama-2-7b-chat.gguf"
echo "  Place in: models/llama-2-7b-chat.gguf"
echo ""
echo "Download complete!"
