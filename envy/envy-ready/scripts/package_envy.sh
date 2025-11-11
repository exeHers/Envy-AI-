#!/bin/bash
# package_envy.sh - Create envy-ready.zip package

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGE_NAME="envy-ready"
PACKAGE_DIR="$ENVY_DIR/$PACKAGE_NAME"
ZIP_FILE="$ENVY_DIR/$PACKAGE_NAME.zip"

echo "=========================================="
echo "Packaging Envy..."
echo "=========================================="

# Clean previous package
rm -rf "$PACKAGE_DIR" "$ZIP_FILE"

# Create package directory
mkdir -p "$PACKAGE_DIR"

# Copy essential files
echo "Copying files..."
[ -d "$ENVY_DIR/src" ] && cp -r "$ENVY_DIR/src" "$PACKAGE_DIR/"
[ -d "$ENVY_DIR/skills" ] && cp -r "$ENVY_DIR/skills" "$PACKAGE_DIR/"
[ -d "$ENVY_DIR/config" ] && cp -r "$ENVY_DIR/config" "$PACKAGE_DIR/"
[ -d "$ENVY_DIR/tests" ] && cp -r "$ENVY_DIR/tests" "$PACKAGE_DIR/"
[ -d "$ENVY_DIR/docs" ] && cp -r "$ENVY_DIR/docs" "$PACKAGE_DIR/"
[ -d "$ENVY_DIR/scripts" ] && cp -r "$ENVY_DIR/scripts" "$PACKAGE_DIR/"

# Copy scripts
cp "$ENVY_DIR/install_envy.sh" "$PACKAGE_DIR/"
cp "$ENVY_DIR/install_envy.bat" "$PACKAGE_DIR/"
cp "$ENVY_DIR/run_envy_local.sh" "$PACKAGE_DIR/"
cp "$ENVY_DIR/run_envy_local.bat" "$PACKAGE_DIR/"
cp "$ENVY_DIR/requirements.txt" "$PACKAGE_DIR/"
cp "$ENVY_DIR/README.md" "$PACKAGE_DIR/"
cp "$ENVY_DIR/LICENSE" "$PACKAGE_DIR/"

# Create artifacts directory structure
mkdir -p "$PACKAGE_DIR/artifacts"/{tests,tts,models}

# Create model download script
cat > "$PACKAGE_DIR/download_models.sh" << 'EOF'
#!/bin/bash
# Download required models

set -e

MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

echo "Downloading VOSK model..."
cd "$MODELS_DIR"
if [ ! -d "vosk-model-small-en-us-0.15" ]; then
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip || {
        echo "WARNING: Could not download VOSK model"
        exit 1
    }
    unzip -q vosk-model-small-en-us-0.15.zip
    rm vosk-model-small-en-us-0.15.zip
    echo "VOSK model downloaded"
else
    echo "VOSK model already exists"
fi

echo "Models ready. Whisper models will be downloaded on first use."
EOF

chmod +x "$PACKAGE_DIR/download_models.sh"

# Create Windows model download script
cat > "$PACKAGE_DIR/download_models.bat" << 'EOF'
@echo off
REM Download required models

if not exist "models" mkdir models
cd models

if not exist "vosk-model-small-en-us-0.15" (
    echo Downloading VOSK model...
    powershell -Command "Invoke-WebRequest -Uri 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip' -OutFile 'vosk-model.zip'"
    powershell -Command "Expand-Archive -Path 'vosk-model.zip' -DestinationPath '.'"
    del vosk-model.zip
    echo VOSK model downloaded
) else (
    echo VOSK model already exists
)

echo Models ready. Whisper models will be downloaded on first use.
EOF

# Make scripts executable
chmod +x "$PACKAGE_DIR"/*.sh

# Create README for package
cat > "$PACKAGE_DIR/PACKAGE_README.txt" << 'EOF'
Envy Personal Assistant - Ready Package
========================================

This package contains all files needed to run Envy.

Quick Start:
1. Run install_envy.sh (Linux) or install_envy.bat (Windows)
2. Run download_models.sh to download required models
3. Run run_envy_local.sh to start Envy

For detailed instructions, see:
- README.md
- docs/install-linux.md
- docs/install-windows.md

System Requirements:
- Python 3.10+
- 16GB RAM
- GTX 1070 (8GB VRAM) recommended but optional
- Linux or Windows 10+

License: MIT (see LICENSE file)
EOF

# Create zip file
echo "Creating zip archive..."
cd "$ENVY_DIR"
zip -r "$ZIP_FILE" "$PACKAGE_NAME" -x "*.pyc" "__pycache__/*" "*.log" "venv/*" ".git/*"

echo ""
echo "=========================================="
echo "Package created: $ZIP_FILE"
echo "=========================================="
echo ""
echo "Package contents:"
ls -lh "$ZIP_FILE"
echo ""
echo "Package size:"
du -sh "$PACKAGE_DIR"
