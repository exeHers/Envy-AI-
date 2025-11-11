#!/bin/bash
# Envy Personal Assistant Installer for Linux

set -e

echo "========================================="
echo "   Envy Personal Assistant Installer"
echo "========================================="
echo ""

# Get base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Parse arguments
LOCAL_DEMO=false
SKIP_MODELS=false

for arg in "$@"; do
    case $arg in
        --local-demo)
            LOCAL_DEMO=true
            shift
            ;;
        --skip-models)
            SKIP_MODELS=true
            shift
            ;;
        *)
            ;;
    esac
done

# Check Python version
echo "1. Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "   Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "2. Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo "   ✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "3. Upgrading pip..."
pip install --quiet --upgrade pip

# Install dependencies
echo ""
echo "4. Installing Python dependencies..."
pip install --quiet -r requirements.txt
echo "   ✓ Dependencies installed"

# Install system dependencies (if needed)
echo ""
echo "5. Checking system dependencies..."

# Check for audio libraries
if ! ldconfig -p | grep -q libportaudio; then
    echo "   Warning: libportaudio not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev python3-pyaudio
    elif command -v yum &> /dev/null; then
        sudo yum install -y portaudio-devel
    else
        echo "   Please install portaudio manually for your system"
    fi
fi

# Check for espeak (for pyttsx3)
if ! command -v espeak &> /dev/null; then
    echo "   Installing espeak for text-to-speech..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y espeak espeak-data
    elif command -v yum &> /dev/null; then
        sudo yum install -y espeak
    fi
fi

echo "   ✓ System dependencies checked"

# Download models
if [ "$SKIP_MODELS" = false ]; then
    echo ""
    echo "6. Downloading AI models..."
    bash scripts/download_models.sh
else
    echo ""
    echo "6. Skipping model download (--skip-models specified)"
fi

# Create necessary directories
echo ""
echo "7. Creating directories..."
mkdir -p logs workspace artifacts/tests config
echo "   ✓ Directories created"

# Make scripts executable
echo ""
echo "8. Setting permissions..."
chmod +x envy_main.py
chmod +x scripts/*.sh
chmod +x run_envy_local.sh 2>/dev/null || true
echo "   ✓ Permissions set"

# Create run script
echo ""
echo "9. Creating run script..."
cat > run_envy_local.sh << 'EOF'
#!/bin/bash
# Start Envy Personal Assistant

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Activate virtual environment
source venv/bin/activate

# Parse arguments
PROFILE="balanced"
NO_GUI=false

for arg in "$@"; do
    case $arg in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --no-gui)
            NO_GUI=true
            shift
            ;;
        *)
            ;;
    esac
done

# Run Envy
echo "Starting Envy Assistant (profile: $PROFILE)..."
if [ "$NO_GUI" = true ]; then
    python3 envy_main.py --profile "$PROFILE" --no-gui
else
    python3 envy_main.py --profile "$PROFILE"
fi
EOF
chmod +x run_envy_local.sh
echo "   ✓ Run script created"

echo ""
echo "========================================="
echo "   Installation Complete!"
echo "========================================="
echo ""
echo "To start Envy:"
echo "   ./run_envy_local.sh"
echo ""
echo "To run tests:"
echo "   source venv/bin/activate"
echo "   python3 -m pytest tests/"
echo ""
echo "To start web dashboard:"
echo "   source venv/bin/activate"
echo "   python3 web/dashboard.py"
echo ""
echo "Configuration file: config/envy.yaml"
echo ""

# Save install log
echo "Installation completed at $(date)" > artifacts/install-log.txt
echo "Python version: $PYTHON_VERSION" >> artifacts/install-log.txt
echo "Base directory: $BASE_DIR" >> artifacts/install-log.txt
