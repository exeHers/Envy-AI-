#!/bin/bash
# Performance reporting script for Envy AI Assistant

echo "======================================================================"
echo "Envy AI Assistant - Performance Report"
echo "======================================================================"
echo ""
echo "Timestamp: $(date)"
echo ""

# Check if envy is running
ENVY_PID=$(pgrep -f "envy_main.py" | head -n 1)

if [ -z "$ENVY_PID" ]; then
    echo "⚠ Envy is not running"
    echo "Start Envy first: ./run_envy_local.sh"
    exit 1
fi

echo "Envy PID: $ENVY_PID"
echo ""

# System information
echo "System Information:"
echo "  OS: $(uname -s) $(uname -r)"
echo "  CPU: $(grep "model name" /proc/cpuinfo | head -n 1 | cut -d: -f2 | xargs)"
echo "  CPU Cores: $(nproc)"
echo "  Total RAM: $(free -h | grep Mem | awk '{print $2}')"
echo ""

# CPU usage
echo "Resource Usage:"
CPU_PERCENT=$(ps -p $ENVY_PID -o %cpu --no-headers | xargs)
echo "  CPU Usage: ${CPU_PERCENT}%"

# Memory usage
MEM_KB=$(ps -p $ENVY_PID -o rss --no-headers | xargs)
MEM_MB=$((MEM_KB / 1024))
echo "  Memory Usage: ${MEM_MB} MB"

# GPU usage (if available)
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "GPU Information:"
    nvidia-smi --query-gpu=gpu_name,memory.total,memory.used,utilization.gpu --format=csv,noheader | while read line; do
        echo "  $line"
    done
fi

echo ""

# Disk usage
echo "Disk Usage:"
echo "  Models directory: $(du -sh models 2>/dev/null | cut -f1)"
echo "  Data directory: $(du -sh data 2>/dev/null | cut -f1)"
echo "  Artifacts directory: $(du -sh artifacts 2>/dev/null | cut -f1)"
echo ""

# Process info
echo "Process Details:"
echo "  Threads: $(ps -p $ENVY_PID -o nlwp --no-headers)"
echo "  Uptime: $(ps -p $ENVY_PID -o etime --no-headers | xargs)"
echo ""

# Latency estimates (from logs if available)
if [ -f "artifacts/logs/envy.log" ]; then
    echo "Recent Activity (last 10 entries):"
    tail -n 10 artifacts/logs/envy.log | while read line; do
        echo "  $line"
    done
fi

echo ""
echo "======================================================================"
