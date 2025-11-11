#!/bin/bash
# Install script for Envy Personal Assistant (Linux)

set -e

ENVY_DIR="${ENVY_DIR:-$(pwd)/envy}"
VENV_DIR="${VENVY_DIR:-$ENVY_DIR/venv}"
PROFILE="${1:-balanced}"

echo "=========================================="
echo "Envy Personal Assistant - Installer"
echo "=========================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.10+ is required"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(printf '%s\n' "3.10" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.10" ]; then
    echo "Error: Python 3.10+ is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo ""
echo "Installing dependencies..."
cd "$ENVY_DIR"
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p "$ENVY_DIR/artifacts"
mkdir -p "$ENVY_DIR/workspace"
mkdir -p "$ENVY_DIR/models"

# Download models (if not present)
echo ""
echo "Checking for models..."

# VOSK model
VOSK_MODEL_DIR="$ENVY_DIR/models/vosk-model-small-en-us-0.22"
if [ ! -d "$VOSK_MODEL_DIR" ]; then
    echo "Downloading VOSK model..."
    cd "$ENVY_DIR/models"
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip || {
        echo "Warning: Failed to download VOSK model. You may need to download it manually."
        echo "URL: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip"
    }
    if [ -f "vosk-model-small-en-us-0.22.zip" ]; then
        unzip -q vosk-model-small-en-us-0.22.zip || true
        rm vosk-model-small-en-us-0.22.zip
    fi
fi

# Whisper models are downloaded automatically by the library
echo "Whisper models will be downloaded automatically on first use."

# LLM model (optional - user can download separately)
echo ""
echo "Note: For local LLM, download a quantized model to $ENVY_DIR/models/"
echo "Recommended: llama-2-7b-chat-q4_0.gguf"
echo "You can use remote free endpoint by enabling it in config/envy.yaml"

# Make scripts executable
chmod +x "$ENVY_DIR/envy.py"
chmod +x "$ENVY_DIR/run_envy_local.sh" 2>/dev/null || true

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "To start Envy:"
echo "  cd $ENVY_DIR"
echo "  source $VENV_DIR/bin/activate"
echo "  python3 envy.py --profile $PROFILE"
echo ""
echo "Or use the run script:"
echo "  ./run_envy_local.sh --profile $PROFILE"
echo ""
