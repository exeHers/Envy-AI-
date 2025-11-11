#!/bin/bash
# Envy AI Assistant - Linux Installer
# Installs dependencies and sets up the environment

set -e

echo "======================================================================"
echo "Envy AI Assistant - Installation Script (Linux)"
echo "======================================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run as root. Run as regular user."
    exit 1
fi

# Detect installation mode
LOCAL_DEMO=false
if [ "$1" == "--local-demo" ]; then
    LOCAL_DEMO=true
    echo "Running in LOCAL DEMO mode (virtualenv)"
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Installation directory: $SCRIPT_DIR"
echo ""

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Check if version is >= 3.8
REQUIRED_VERSION="3.8"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "Error: Python 3.8 or higher is required"
    exit 1
fi
echo "✓ Python version OK"
echo ""

# Step 2: Create virtual environment (if local demo)
if [ "$LOCAL_DEMO" = true ]; then
    echo "Step 2: Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✓ Virtual environment created"
    else
        echo "✓ Virtual environment already exists"
    fi
    
    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo ""
fi

# Step 3: Install system dependencies
echo "Step 3: Installing system dependencies..."
echo "Detecting package manager..."

if command -v apt-get &> /dev/null; then
    echo "Using apt-get..."
    sudo apt-get update
    sudo apt-get install -y \
        portaudio19-dev \
        python3-pyaudio \
        ffmpeg \
        espeak \
        alsa-utils \
        libsndfile1
    echo "✓ System dependencies installed"
elif command -v dnf &> /dev/null; then
    echo "Using dnf..."
    sudo dnf install -y \
        portaudio-devel \
        python3-pyaudio \
        ffmpeg \
        espeak \
        alsa-utils \
        libsndfile
    echo "✓ System dependencies installed"
elif command -v pacman &> /dev/null; then
    echo "Using pacman..."
    sudo pacman -S --noconfirm \
        portaudio \
        python-pyaudio \
        ffmpeg \
        espeak \
        alsa-utils \
        libsndfile
    echo "✓ System dependencies installed"
else
    echo "⚠ Could not detect package manager"
    echo "Please manually install: portaudio, ffmpeg, espeak, alsa-utils"
fi
echo ""

# Step 4: Install Python dependencies
echo "Step 4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

# Step 5: Create directories
echo "Step 5: Creating directories..."
mkdir -p models
mkdir -p data
mkdir -p workspace
mkdir -p artifacts/{tests,logs,research}
echo "✓ Directories created"
echo ""

# Step 6: Download models
echo "Step 6: Downloading AI models..."
echo "This may take several minutes..."

# Download VOSK model for wake word
if [ ! -d "models/vosk-model-small-en-us-0.15" ]; then
    echo "Downloading VOSK model..."
    wget -q --show-progress -O models/vosk-model.zip \
        https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip -q models/vosk-model.zip -d models/
    rm models/vosk-model.zip
    echo "✓ VOSK model downloaded"
else
    echo "✓ VOSK model already exists"
fi

# Download TinyLlama model (optional, can be downloaded on first run)
if [ ! -f "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo "Downloading TinyLlama model (670MB)..."
    echo "This may take 5-10 minutes depending on your connection..."
    wget -q --show-progress -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
        https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf || {
        echo "⚠ Model download failed - will download on first run"
    }
    
    if [ -f "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
        echo "✓ TinyLlama model downloaded"
    fi
else
    echo "✓ TinyLlama model already exists"
fi

echo ""

# Step 7: Test installation
echo "Step 7: Testing installation..."
if python3 -c "import yaml; import sounddevice; import pyttsx3; print('✓ Core modules OK')" 2>/dev/null; then
    echo "✓ Installation test passed"
else
    echo "⚠ Some modules may not be working correctly"
fi
echo ""

# Step 8: Create run scripts
echo "Step 8: Creating run scripts..."

cat > run_envy_local.sh << 'EOF'
#!/bin/bash
# Run Envy AI Assistant locally

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Parse arguments
PROFILE="${1:-balanced}"
if [ "$1" == "--profile" ]; then
    PROFILE="$2"
fi

echo "Starting Envy AI Assistant (profile: $PROFILE)..."
python3 envy_main.py --config config/envy.yaml --profile "$PROFILE"
EOF

chmod +x run_envy_local.sh
echo "✓ Run script created: run_envy_local.sh"
echo ""

# Installation complete
echo "======================================================================"
echo "✓ Installation Complete!"
echo "======================================================================"
echo ""
echo "To start Envy AI Assistant:"
echo "  ./run_envy_local.sh"
echo ""
echo "To run tests:"
echo "  bash tests/run_all_tests.sh"
echo ""
echo "To access the web dashboard (after starting):"
echo "  http://localhost:8080"
echo ""
echo "Configuration file:"
echo "  config/envy.yaml"
echo ""
echo "======================================================================"

# Save installation log
LOG_FILE="artifacts/install-log.txt"
echo "Installation completed at $(date)" > "$LOG_FILE"
echo "Python version: $PYTHON_VERSION" >> "$LOG_FILE"
echo "Installation directory: $SCRIPT_DIR" >> "$LOG_FILE"
echo "Local demo mode: $LOCAL_DEMO" >> "$LOG_FILE"
echo "✓ Installation log saved: $LOG_FILE"
