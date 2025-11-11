#!/bin/bash
# package_envy.sh - Create final distribution package
set -e

ENVY_DIR="${ENVY_DIR:-$(pwd)}"
PACKAGE_NAME="envy-ready"
PACKAGE_DIR="/workspace/${PACKAGE_NAME}"
ZIP_FILE="/workspace/${PACKAGE_NAME}.zip"

echo "=========================================="
echo "Packaging Envy for Distribution"
echo "=========================================="

# Clean previous package
if [ -d "$PACKAGE_DIR" ]; then
    rm -rf "$PACKAGE_DIR"
fi
if [ -f "$ZIP_FILE" ]; then
    rm -f "$ZIP_FILE"
fi

# Create package directory
mkdir -p "$PACKAGE_DIR"

echo "Copying files..."

# Copy source files
cp -r "$ENVY_DIR/config" "$PACKAGE_DIR/"
cp -r "$ENVY_DIR/services" "$PACKAGE_DIR/"
cp -r "$ENVY_DIR/skills" "$PACKAGE_DIR/"
cp -r "$ENVY_DIR/web" "$PACKAGE_DIR/"
cp -r "$ENVY_DIR/scripts" "$PACKAGE_DIR/"
cp -r "$ENVY_DIR/docs" "$PACKAGE_DIR/"

# Copy main files
cp "$ENVY_DIR/envy.py" "$PACKAGE_DIR/"
cp "$ENVY_DIR/main.py" "$PACKAGE_DIR/"
cp "$ENVY_DIR/requirements.txt" "$PACKAGE_DIR/"
cp "$ENVY_DIR/LICENSE" "$PACKAGE_DIR/"
cp "$ENVY_DIR/README.md" "$PACKAGE_DIR/"

# Create artifacts directory
mkdir -p "$PACKAGE_DIR/artifacts/tests"
mkdir -p "$PACKAGE_DIR/artifacts/tts-output"
mkdir -p "$PACKAGE_DIR/models"

# Create run script
cat > "$PACKAGE_DIR/run_envy_local.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running installer..."
    bash scripts/install_envy.sh --local-demo
fi

source venv/bin/activate
python main.py "$@"
EOF
chmod +x "$PACKAGE_DIR/run_envy_local.sh"

# Create Windows run script
cat > "$PACKAGE_DIR/run_envy_local.bat" << 'EOF'
@echo off
cd /d "%~dp0"

if not exist "venv" (
    echo Virtual environment not found. Running installer...
    call scripts\install_envy.bat --local-demo
)

call venv\Scripts\activate.bat
python main.py %*
EOF

# Create quick start guide
cat > "$PACKAGE_DIR/QUICKSTART.txt" << 'EOF'
ENVY PERSONAL ASSISTANT - QUICK START
=====================================

1. INSTALLATION:
   Linux/Mac: bash scripts/install_envy.sh --local-demo
   Windows:   scripts\install_envy.bat --local-demo

2. RUN:
   Linux/Mac: ./run_envy_local.sh
   Windows:   run_envy_local.bat

3. ACCESS DASHBOARD:
   Open browser to: http://localhost:8080

4. TEST:
   Linux/Mac: ./scripts/run_tests.sh
   Windows:   Use Git Bash or WSL for tests

5. CONFIGURE:
   Edit config/envy.yaml to customize settings

For detailed instructions, see docs/install-linux.md or docs/install-windows.md
EOF

# Create package info
cat > "$PACKAGE_DIR/PACKAGE_INFO.txt" << EOF
Envy Personal Assistant Distribution
Generated: $(date)
Version: 1.0.0

Contents:
- Source code (services/, skills/, web/)
- Configuration (config/)
- Installation scripts (scripts/)
- Documentation (docs/)
- Run scripts (run_envy_local.sh/bat)

To install:
1. Extract this package
2. Run installer script
3. Start with run_envy_local.sh/bat

See README.md for full documentation.
EOF

# Create zip file
echo "Creating zip archive..."
cd /workspace
zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}" -q

echo ""
echo "=========================================="
echo "Package created: ${ZIP_FILE}"
echo "=========================================="
echo ""
echo "Package contents:"
ls -lh "$ZIP_FILE"
echo ""
echo "Package structure:"
tree -L 2 "$PACKAGE_DIR" || find "$PACKAGE_DIR" -maxdepth 2 -type f -o -type d | head -20
echo ""
