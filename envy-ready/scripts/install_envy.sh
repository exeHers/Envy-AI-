#!/bin/bash
# install_envy.sh - Installer for Envy Personal Assistant
set -e

ENVY_DIR="${ENVY_DIR:-$(pwd)}"
VENV_DIR="${VENVY_DIR:-$ENVY_DIR/venv}"
PYTHON_CMD="${PYTHON_CMD:-python3}"

echo "=========================================="
echo "Envy Personal Assistant - Installer"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
cd "$ENVY_DIR"
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p models artifacts/tests artifacts/tts-output config skills

# Download models if needed
if [ "$1" == "--local-demo" ] || [ "$1" == "--download-models" ]; then
    echo "Downloading models..."
    if [ -f "scripts/download_models.sh" ]; then
        bash scripts/download_models.sh
    else
        echo "Model download script not found. Skipping model download."
        echo "Run scripts/download_models.sh manually to download models."
    fi
fi

# Install systemd service (if root)
if [ "$EUID" -eq 0 ] && [ -f "scripts/envy.service" ]; then
    echo "Installing systemd service..."
    cp scripts/envy.service /etc/systemd/system/
    systemctl daemon-reload
    echo "Service installed. Use 'systemctl start envy' to start."
else
    echo "Not running as root. Skipping systemd service installation."
    echo "To install service manually, copy scripts/envy.service to /etc/systemd/system/"
fi

# Create run script
echo "Creating run script..."
cat > "$ENVY_DIR/run_envy_local.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py "$@"
EOF
chmod +x "$ENVY_DIR/run_envy_local.sh"

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "To start Envy:"
echo "  ./run_envy_local.sh"
echo ""
echo "To start with web dashboard:"
echo "  ./run_envy_local.sh --host 0.0.0.0"
echo ""
echo "To run tests:"
echo "  ./scripts/run_tests.sh"
echo ""
