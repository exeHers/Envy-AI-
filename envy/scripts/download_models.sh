#!/bin/bash
# Download AI models for Envy AI Assistant

set -e

echo "======================================================================"
echo "Envy AI Assistant - Model Downloader"
echo "======================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Create models directory
mkdir -p models

# Download VOSK model
echo "1. Downloading VOSK model for wake word detection..."
if [ ! -d "models/vosk-model-small-en-us-0.15" ]; then
    echo "   Downloading VOSK small model (40MB)..."
    wget -q --show-progress -O models/vosk-model.zip \
        https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    
    echo "   Extracting..."
    unzip -q models/vosk-model.zip -d models/
    rm models/vosk-model.zip
    
    echo "   ✓ VOSK model downloaded"
else
    echo "   ✓ VOSK model already exists"
fi
echo ""

# Download TinyLlama model
echo "2. Downloading TinyLlama LLM model..."
if [ ! -f "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo "   Downloading TinyLlama 1.1B Q4 model (670MB)..."
    echo "   This may take 5-10 minutes..."
    wget -q --show-progress -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
        https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
    
    echo "   ✓ TinyLlama model downloaded"
else
    echo "   ✓ TinyLlama model already exists"
fi
echo ""

# Optional: Download larger models
read -p "Download optional larger models? (Mistral 7B - 4.1GB) [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "3. Downloading Mistral 7B model (optional)..."
    if [ ! -f "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf" ]; then
        echo "   Downloading Mistral 7B Q4 model (4.1GB)..."
        echo "   This will take 10-20 minutes..."
        wget -q --show-progress -O models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
            https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
        
        echo "   ✓ Mistral 7B model downloaded"
        echo ""
        echo "   To use Mistral, update config/envy.yaml:"
        echo "   llm:"
        echo "     local:"
        echo "       model_path: \"./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf\""
    else
        echo "   ✓ Mistral 7B model already exists"
    fi
fi
echo ""

echo "======================================================================"
echo "✓ Model download complete!"
echo "======================================================================"
echo ""
echo "Downloaded models:"
ls -lh models/
echo ""
