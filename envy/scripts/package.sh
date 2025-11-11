#!/bin/bash
# Package Envy into envy-ready.zip

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(dirname "$ENVY_DIR")"
OUTPUT_ZIP="$WORKSPACE_ROOT/envy-ready.zip"

echo "=========================================="
echo "Packaging Envy..."
echo "=========================================="

cd "$ENVY_DIR"

# Clean previous builds
rm -f "$OUTPUT_ZIP"
rm -rf artifacts/tests/*.log artifacts/*.wav 2>/dev/null || true

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/envy"

mkdir -p "$PACKAGE_DIR"

echo "Copying files..."

# Copy core files (check if they exist first)
[ -d "config" ] && cp -r config "$PACKAGE_DIR/"
[ -d "skills" ] && cp -r skills "$PACKAGE_DIR/"
[ -d "services" ] && cp -r services "$PACKAGE_DIR/"
[ -d "web" ] && cp -r web "$PACKAGE_DIR/"
[ -d "scripts" ] && cp -r scripts "$PACKAGE_DIR/"
[ -d "docs" ] && cp -r docs "$PACKAGE_DIR/"

# Copy main files
cp envy.py "$PACKAGE_DIR/"
cp requirements.txt "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"
cp LICENSE "$PACKAGE_DIR/"

# Copy installers
cp install_envy.sh "$PACKAGE_DIR/"
cp install_envy.bat "$PACKAGE_DIR/"
cp run_envy_local.sh "$PACKAGE_DIR/"
cp run_envy_local.bat "$PACKAGE_DIR/"

# Make scripts executable
chmod +x "$PACKAGE_DIR"/*.sh "$PACKAGE_DIR"/*.py "$PACKAGE_DIR"/scripts/*.sh 2>/dev/null || true

# Create directories
mkdir -p "$PACKAGE_DIR/artifacts/tests"
mkdir -p "$PACKAGE_DIR/workspace"
mkdir -p "$PACKAGE_DIR/models"

# Create model download script
cat > "$PACKAGE_DIR/download_models.sh" << 'EOF'
#!/bin/bash
# Download required models

set -e

MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

echo "Downloading VOSK model..."
cd "$MODELS_DIR"
if [ ! -d "vosk-model-small-en-us-0.22" ]; then
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip || {
        echo "Warning: Failed to download VOSK model"
        exit 1
    }
    unzip -q vosk-model-small-en-us-0.22.zip
    rm vosk-model-small-en-us-0.22.zip
fi

echo "VOSK model downloaded"
echo ""
echo "Note: Whisper models download automatically on first use"
echo "For LLM: Download a quantized model (e.g., llama-2-7b-chat-q4_0.gguf) to models/"
EOF

chmod +x "$PACKAGE_DIR/download_models.sh"

# Create README for package
cat > "$PACKAGE_DIR/PACKAGE_README.txt" << 'EOF'
Envy Personal Assistant - Ready Package
========================================

Quick Start:
1. Extract this package
2. Run: ./install_envy.sh (Linux) or install_envy.bat (Windows)
3. Run: ./run_envy_local.sh --profile balanced

For detailed instructions, see:
- README.md
- docs/install-linux.md
- docs/install-windows.md

Models:
- VOSK model: Run ./download_models.sh
- Whisper: Downloads automatically
- LLM: Download manually or use remote free endpoint

Web Dashboard: http://127.0.0.1:8080
EOF

# Create zip
echo "Creating zip archive..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_ZIP" envy > /dev/null

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "=========================================="
echo "Package created: $OUTPUT_ZIP"
echo "=========================================="
echo ""
echo "Contents:"
unzip -l "$OUTPUT_ZIP" | head -20
echo "..."
echo ""
echo "Package size: $(du -h "$OUTPUT_ZIP" | cut -f1)"
