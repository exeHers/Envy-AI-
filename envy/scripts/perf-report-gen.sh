#!/bin/bash
# Performance monitoring script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$SCRIPT_DIR/.."
REPORT_FILE="$ENVY_DIR/artifacts/perf-report.txt"

echo "==========================================" > "$REPORT_FILE"
echo "Envy Performance Report" >> "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
echo "==========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# CPU Info
echo "CPU Information:" >> "$REPORT_FILE"
if command -v lscpu &> /dev/null; then
    lscpu | grep -E "Model name|CPU\(s\)|Thread|Core" >> "$REPORT_FILE"
elif [ -f /proc/cpuinfo ]; then
    grep -m 1 "model name" /proc/cpuinfo >> "$REPORT_FILE"
    grep -c "processor" /proc/cpuinfo | xargs echo "CPU cores:" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Memory Info
echo "Memory Information:" >> "$REPORT_FILE"
if command -v free &> /dev/null; then
    free -h >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# GPU Info
echo "GPU Information:" >> "$REPORT_FILE"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader >> "$REPORT_FILE"
else
    echo "NVIDIA GPU not detected or nvidia-smi not available" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Python version
echo "Python Version:" >> "$REPORT_FILE"
python3 --version >> "$REPORT_FILE" 2>&1 || echo "Python not found" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Check installed packages
echo "Key Package Versions:" >> "$REPORT_FILE"
python3 -c "
try:
    import torch
    print(f'torch: {torch.__version__}')
except:
    print('torch: not installed')
try:
    import whisper
    print(f'whisper: installed')
except:
    print('whisper: not installed')
try:
    import vosk
    print(f'vosk: installed')
except:
    print('vosk: not installed')
try:
    import llama_cpp
    print(f'llama-cpp-python: installed')
except:
    print('llama-cpp-python: not installed')
" >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# Resource recommendations
echo "Resource Recommendations:" >> "$REPORT_FILE"
echo "- For Intel i3 + GTX 1070 (8GB VRAM):" >> "$REPORT_FILE"
echo "  * Use 'balanced' profile" >> "$REPORT_FILE"
echo "  * Whisper model: base" >> "$REPORT_FILE"
echo "  * LLM: quantized q4_0 model (7B parameters)" >> "$REPORT_FILE"
echo "  * GPU layers: 20-25" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

cat "$REPORT_FILE"
echo ""
echo "Report saved to: $REPORT_FILE"
