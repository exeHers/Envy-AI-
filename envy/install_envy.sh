#!/bin/bash
# Envy Installation Script for Linux
# MIT License

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "🤖 Envy Personal Assistant - Installer"
echo "========================================="
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Found Python $PYTHON_VERSION"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi
echo "✓ pip3 found"

# Create virtual environment
echo ""
echo "[2/6] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "[3/6] Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo ""
echo "[4/6] Installing Python dependencies..."
echo "This may take several minutes..."
pip install -r requirements.txt

# Install system dependencies
echo ""
echo "[5/6] Checking system dependencies..."

# Check for audio libraries
if command -v apt-get &> /dev/null; then
    echo "Detected Debian/Ubuntu system"
    echo "You may need to install: sudo apt-get install portaudio19-dev python3-pyaudio ffmpeg"
elif command -v yum &> /dev/null; then
    echo "Detected RedHat/CentOS system"
    echo "You may need to install: sudo yum install portaudio-devel python3-pyaudio ffmpeg"
fi

# Create necessary directories
echo ""
echo "[6/6] Setting up directories..."
mkdir -p artifacts/logs
mkdir -p artifacts/tests
mkdir -p artifacts/research
mkdir -p models

# Download models
echo ""
echo "========================================="
read -p "Download required models now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    chmod +x scripts/download_models.sh
    ./scripts/download_models.sh
else
    echo "⚠ Skipping model download. Run 'scripts/download_models.sh' later."
fi

# Make main.py executable
chmod +x main.py

echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "To start Envy:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python main.py"
echo ""
echo "Or use the quick-start script: ./run_envy_local.sh"
echo ""
echo "Web dashboard will be available at: http://localhost:8080"
echo ""
