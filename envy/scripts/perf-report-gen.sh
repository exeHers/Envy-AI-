#!/bin/bash
# perf-report-gen.sh - Generate performance report

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$SCRIPT_DIR/.."
REPORT_FILE="$ENVY_DIR/artifacts/perf-report.txt"

echo "Generating performance report..." > "$REPORT_FILE"
echo "Timestamp: $(date)" >> "$REPORT_FILE"
echo "==========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# CPU Info
echo "CPU Information:" >> "$REPORT_FILE"
if command -v lscpu &> /dev/null; then
    lscpu | grep -E "Model name|CPU\(s\)|Thread|Core" >> "$REPORT_FILE"
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
    echo "No NVIDIA GPU detected" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Python version
echo "Python Version:" >> "$REPORT_FILE"
python3 --version >> "$REPORT_FILE" 2>&1 || python --version >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# System load
echo "System Load:" >> "$REPORT_FILE"
if command -v uptime &> /dev/null; then
    uptime >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

echo "Performance report generated: $REPORT_FILE"
cat "$REPORT_FILE"
