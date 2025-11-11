#!/bin/bash
# Install Envy Personal Assistant on Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Envy Personal Assistant Installer"
echo "========================================"
echo ""

# Check for Python 3.10+
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Check version is >= 3.10
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ $MAJOR -lt 3 ] || ([ $MAJOR -eq 3 ] && [ $MINOR -lt 10 ]); then
    echo "Error: Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python version OK"
echo ""

# Check for virtual environment or create one
VENV_DIR="$BASE_DIR/venv"

if [ "$1" == "--local-demo" ]; then
    echo "Local demo mode: creating virtual environment..."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

echo ""
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo ""
echo "Installing dependencies..."
cd "$BASE_DIR"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "✓ Dependencies installed"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p "$BASE_DIR"/{logs,data,workspace,artifacts/tests}
echo "✓ Directories created"

# Download models
echo ""
read -p "Download models now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash "$SCRIPT_DIR/download_models.sh"
else
    echo "Skipping model download. Run ./installers/download_models.sh later."
fi

# Create run scripts
echo ""
echo "Creating run scripts..."

cat > "$BASE_DIR/run_envy_local.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
cd "$SCRIPT_DIR"
python3 envy_main.py "$@"
EOF
chmod +x "$BASE_DIR/run_envy_local.sh"

cat > "$BASE_DIR/start-envy.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
cd "$SCRIPT_DIR"
python3 envy_main.py --profile balanced
EOF
chmod +x "$BASE_DIR/start-envy.sh"

echo "✓ Run scripts created"

# Optionally install systemd service
echo ""
read -p "Install systemd service? (requires sudo) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/envy.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Envy Personal Assistant
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BASE_DIR
ExecStart=$BASE_DIR/venv/bin/python3 $BASE_DIR/envy_main.py --profile balanced
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    echo "✓ Systemd service installed"
    echo ""
    echo "To start Envy as a service:"
    echo "  sudo systemctl start envy"
    echo "  sudo systemctl enable envy  # Start on boot"
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "To run Envy:"
echo "  ./run_envy_local.sh --profile balanced"
echo ""
echo "Or simply:"
echo "  ./start-envy.sh"
echo ""
echo "To run tests:"
echo "  source venv/bin/activate"
echo "  pytest tests/"
echo ""
echo "Dashboard will be available at: http://127.0.0.1:8080"
echo ""
