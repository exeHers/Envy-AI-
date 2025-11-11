#!/bin/bash
# build_and_test.sh - Build and test Envy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$SCRIPT_DIR"
LOG_FILE="$ENVY_DIR/artifacts/build-log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "$ENVY_DIR/artifacts"/{tests,tts,models}

echo "==========================================" | tee -a "$LOG_FILE"
echo "Envy Build and Test - $TIMESTAMP" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

# Step 1: Install dependencies
echo "" | tee -a "$LOG_FILE"
echo "Step 1: Installing dependencies..." | tee -a "$LOG_FILE"
if [ -d "$ENVY_DIR/venv" ]; then
    source "$ENVY_DIR/venv/bin/activate"
else
    echo "Creating virtual environment..." | tee -a "$LOG_FILE"
    python3 -m venv "$ENVY_DIR/venv"
    source "$ENVY_DIR/venv/bin/activate"
    pip install --upgrade pip setuptools wheel
fi

pip install -q -r "$ENVY_DIR/requirements.txt" 2>&1 | tee -a "$LOG_FILE" || {
    echo "Installing core dependencies..." | tee -a "$LOG_FILE"
    pip install -q sounddevice vosk openai-whisper pyttsx3 fastapi uvicorn websockets pyyaml requests numpy psutil 2>&1 | tee -a "$LOG_FILE"
}

# Step 2: Generate performance report
echo "" | tee -a "$LOG_FILE"
echo "Step 2: Generating performance report..." | tee -a "$LOG_FILE"
bash "$ENVY_DIR/scripts/perf-report-gen.sh" 2>&1 | tee -a "$LOG_FILE"

# Step 3: Run tests
echo "" | tee -a "$LOG_FILE"
echo "Step 3: Running tests..." | tee -a "$LOG_FILE"
cd "$ENVY_DIR"
python3 tests/test_envy.py 2>&1 | tee -a "$LOG_FILE" || {
    echo "WARNING: Some tests failed, but continuing..." | tee -a "$LOG_FILE"
}

# Step 4: Package
echo "" | tee -a "$LOG_FILE"
echo "Step 4: Creating package..." | tee -a "$LOG_FILE"
bash "$ENVY_DIR/scripts/package_envy.sh" 2>&1 | tee -a "$LOG_FILE"

# Step 5: Summary
echo "" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "Build Summary" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "Build log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Test results: $ENVY_DIR/artifacts/tests/test_results.json" | tee -a "$LOG_FILE"
echo "Performance report: $ENVY_DIR/artifacts/perf-report.txt" | tee -a "$LOG_FILE"

if [ -f "$ENVY_DIR/envy-ready.zip" ]; then
    echo "Package created: $ENVY_DIR/envy-ready.zip" | tee -a "$LOG_FILE"
    echo "PASS: Package created successfully" | tee -a "$LOG_FILE"
else
    echo "FAIL: Package not created" | tee -a "$LOG_FILE"
    exit 1
fi

echo "Build completed at $(date)" | tee -a "$LOG_FILE"
