#!/bin/bash
# Generate performance report for Envy

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$SCRIPT_DIR/perf-report.txt"

echo "========================================"
echo "Envy Performance Report"
echo "========================================"
echo "Generated: $(date)" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# System info
echo "System Information:" >> "$OUTPUT_FILE"
echo "  OS: $(uname -s -r)" >> "$OUTPUT_FILE"
echo "  CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)" >> "$OUTPUT_FILE"
echo "  Memory: $(free -h | grep Mem | awk '{print $2}')" >> "$OUTPUT_FILE"

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)" >> "$OUTPUT_FILE"
    echo "  GPU Memory: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader)" >> "$OUTPUT_FILE"
else
    echo "  GPU: None detected" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"

# Python environment
echo "Python Environment:" >> "$OUTPUT_FILE"
echo "  Python: $(python3 --version)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Envy metrics (if available)
echo "Envy Metrics:" >> "$OUTPUT_FILE"

# Check if Envy is running
if pgrep -f "envy_main.py" > /dev/null; then
    PID=$(pgrep -f "envy_main.py")
    echo "  Status: Running (PID: $PID)" >> "$OUTPUT_FILE"
    
    # Get CPU and memory usage
    if command -v ps &> /dev/null; then
        CPU=$(ps -p $PID -o %cpu= | xargs)
        MEM=$(ps -p $PID -o %mem= | xargs)
        RSS=$(ps -p $PID -o rss= | xargs)
        
        echo "  CPU Usage: ${CPU}%" >> "$OUTPUT_FILE"
        echo "  Memory Usage: ${MEM}%" >> "$OUTPUT_FILE"
        echo "  Memory (RSS): $((RSS / 1024)) MB" >> "$OUTPUT_FILE"
    fi
else
    echo "  Status: Not running" >> "$OUTPUT_FILE"
    echo "  Note: Start Envy to measure runtime performance" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"

# Estimated resource requirements
echo "Estimated Resource Requirements:" >> "$OUTPUT_FILE"
echo "  Profile: Balanced" >> "$OUTPUT_FILE"
echo "  CPU: ~40-60% (4 threads)" >> "$OUTPUT_FILE"
echo "  RAM: ~2-4 GB" >> "$OUTPUT_FILE"
echo "  GPU VRAM: ~2-4 GB (if using GPU)" >> "$OUTPUT_FILE"
echo "  Wake-word listener: ~5-10% CPU (idle)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Latency estimates
echo "Typical Latency:" >> "$OUTPUT_FILE"
echo "  Wake word detection: ~100-300ms" >> "$OUTPUT_FILE"
echo "  Speech-to-text (5s audio): ~500-2000ms" >> "$OUTPUT_FILE"
echo "  LLM inference: ~500-3000ms (depends on model)" >> "$OUTPUT_FILE"
echo "  Text-to-speech: ~100-500ms" >> "$OUTPUT_FILE"
echo "  Total (wake → response): ~2-6 seconds" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "========================================"
echo "Performance report generated: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
