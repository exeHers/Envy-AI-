#!/bin/bash
# perf-report-gen.sh - Generate performance report
set -e

ENVY_DIR="${ENVY_DIR:-$(pwd)}"
ARTIFACTS_DIR="$ENVY_DIR/artifacts"
REPORT_FILE="$ARTIFACTS_DIR/perf-report.txt"

echo "Generating performance report..."
echo "Report will be saved to: $REPORT_FILE"

{
    echo "=========================================="
    echo "Envy Performance Report"
    echo "Generated: $(date)"
    echo "=========================================="
    echo ""
    
    # CPU Info
    echo "CPU Information:"
    if [ -f /proc/cpuinfo ]; then
        echo "  Model: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
        echo "  Cores: $(nproc)"
    else
        echo "  CPU info not available"
    fi
    echo ""
    
    # Memory Info
    echo "Memory Information:"
    if command -v free &> /dev/null; then
        free -h | head -2
    else
        echo "  Memory info not available"
    fi
    echo ""
    
    # GPU Info
    echo "GPU Information:"
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader | head -1
    else
        echo "  No NVIDIA GPU detected (or nvidia-smi not available)"
    fi
    echo ""
    
    # Python version
    echo "Python Version:"
    python3 --version 2>&1 || echo "  Python not found"
    echo ""
    
    # Package versions
    echo "Key Package Versions:"
    if [ -d "$ENVY_DIR/venv" ]; then
        source "$ENVY_DIR/venv/bin/activate"
        pip list | grep -E "(whisper|vosk|fastapi|llama)" || echo "  Packages not installed"
    fi
    echo ""
    
    echo "=========================================="
    echo "Note: Runtime performance metrics would"
    echo "be captured during actual execution."
    echo "=========================================="
    
} > "$REPORT_FILE"

echo "Performance report generated: $REPORT_FILE"
cat "$REPORT_FILE"
