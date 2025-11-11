#!/bin/bash
# install_envy.sh - Installer for Envy Personal Assistant (Linux)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$SCRIPT_DIR"
VENV_DIR="$ENVY_DIR/venv"

echo "=========================================="
echo "Envy Personal Assistant - Installer"
echo "=========================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3.10+ is required"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -r "$ENVY_DIR/requirements.txt" || {
    echo "Installing core dependencies..."
    pip install \
        sounddevice \
        vosk \
        openai-whisper \
        pyttsx3 \
        fastapi \
        uvicorn \
        websockets \
        pyyaml \
        requests \
        numpy \
        psutil
}

# Download models
echo "Downloading models..."
MODELS_DIR="$ENVY_DIR/models"
mkdir -p "$MODELS_DIR"

# Download VOSK model if not exists
VOSK_MODEL="$MODELS_DIR/vosk-model-small-en-us-0.15"
if [ ! -d "$VOSK_MODEL" ]; then
    echo "Downloading VOSK model..."
    cd "$MODELS_DIR"
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip || {
        echo "WARNING: Could not download VOSK model. You may need to download it manually."
    }
    if [ -f "vosk-model-small-en-us-0.15.zip" ]; then
        unzip -q vosk-model-small-en-us-0.15.zip
        rm vosk-model-small-en-us-0.15.zip
    fi
fi

# Download Whisper model (will be downloaded on first use, but we can prepare)
echo "Whisper models will be downloaded automatically on first use."

# Create systemd service (optional)
if [ "$1" == "--systemd" ]; then
    echo "Creating systemd service..."
    SERVICE_FILE="/etc/systemd/system/envy.service"
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Envy Personal Assistant
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$ENVY_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python $ENVY_DIR/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    echo "Systemd service created. Enable with: sudo systemctl enable envy"
fi

# Create artifacts directory
mkdir -p "$ENVY_DIR/artifacts"/{tests,tts,models}

# Set permissions
chmod +x "$ENVY_DIR/src/main.py"
chmod +x "$ENVY_DIR/run_envy_local.sh"

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "To run Envy:"
echo "  cd $ENVY_DIR"
echo "  source venv/bin/activate"
echo "  ./run_envy_local.sh"
echo ""
echo "Or use the systemd service:"
echo "  sudo systemctl start envy"
echo "  sudo systemctl enable envy"
echo ""
