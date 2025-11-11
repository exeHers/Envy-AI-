#!/bin/bash
# Envy installer for Linux

set -e

echo "=========================================="
echo "Envy Personal Assistant - Linux Installer"
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

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENVY_DIR="$SCRIPT_DIR"

cd "$ENVY_DIR"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download VOSK model if not present
VOSK_MODEL_DIR="models/vosk-model-small-en-us-0.15"
if [ ! -d "$VOSK_MODEL_DIR" ]; then
    echo "Downloading VOSK model..."
    mkdir -p models
    cd models
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip -q vosk-model-small-en-us-0.15.zip
    rm vosk-model-small-en-us-0.15.zip
    cd ..
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p artifacts/{tests,tts}
mkdir -p logs

# Set permissions
chmod +x main.py
chmod +x scripts/*.sh 2>/dev/null || true

# Install systemd service (optional)
if [ "$1" == "--install-service" ]; then
    echo "Installing systemd service..."
    sudo cp scripts/envy.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable envy.service
    echo "Service installed. Start with: sudo systemctl start envy"
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "To run Envy:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or use the run script:"
echo "  ./run_envy_local.sh"
echo ""
