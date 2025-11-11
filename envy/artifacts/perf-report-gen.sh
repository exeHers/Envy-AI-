#!/bin/bash
# Generate performance report for Envy
# MIT License

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPORT_FILE="$SCRIPT_DIR/perf-report.txt"

echo "=========================================" > "$REPORT_FILE"
echo "Envy Performance Report" >> "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
echo "=========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# System Info
echo "System Information:" >> "$REPORT_FILE"
echo "-------------------" >> "$REPORT_FILE"
uname -a >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# CPU Info
echo "CPU Information:" >> "$REPORT_FILE"
echo "----------------" >> "$REPORT_FILE"
if command -v lscpu &> /dev/null; then
    lscpu | grep -E "Model name|CPU\(s\)|Thread|MHz" >> "$REPORT_FILE" 2>&1
else
    echo "lscpu not available" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Memory Info
echo "Memory Information:" >> "$REPORT_FILE"
echo "-------------------" >> "$REPORT_FILE"
if command -v free &> /dev/null; then
    free -h >> "$REPORT_FILE" 2>&1
else
    echo "free command not available" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# GPU Info
echo "GPU Information:" >> "$REPORT_FILE"
echo "----------------" >> "$REPORT_FILE"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv >> "$REPORT_FILE" 2>&1
else
    echo "nvidia-smi not available (no NVIDIA GPU detected)" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Process Info (if Envy is running)
echo "Process Information:" >> "$REPORT_FILE"
echo "--------------------" >> "$REPORT_FILE"
if pgrep -f "main.py" > /dev/null; then
    ps aux | grep -E "main.py|PID" | grep -v grep >> "$REPORT_FILE" 2>&1
    echo "" >> "$REPORT_FILE"
    
    # Get CPU and memory usage
    PID=$(pgrep -f "main.py" | head -1)
    if [ ! -z "$PID" ]; then
        echo "Resource usage for PID $PID:" >> "$REPORT_FILE"
        top -b -n 1 -p $PID | tail -2 >> "$REPORT_FILE" 2>&1
    fi
else
    echo "Envy is not currently running" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Estimated latency metrics
echo "Estimated Latency Metrics:" >> "$REPORT_FILE"
echo "--------------------------" >> "$REPORT_FILE"
echo "Wake word detection: ~100-200ms (VOSK)" >> "$REPORT_FILE"
echo "STT processing: ~1-3s (Whisper base model)" >> "$REPORT_FILE"
echo "LLM inference: 2-10s (depending on model and hardware)" >> "$REPORT_FILE"
echo "TTS synthesis: ~0.5-1s (pyttsx3)" >> "$REPORT_FILE"
echo "Total wake->response: ~4-15s (typical)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "=========================================" >> "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE" >> "$REPORT_FILE"
echo "=========================================" >> "$REPORT_FILE"

# Also output to console
cat "$REPORT_FILE"
