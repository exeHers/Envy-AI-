#!/bin/bash
# Performance report generator

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

mkdir -p artifacts
REPORT_FILE="artifacts/perf-report.txt"

echo "==========================================" > "$REPORT_FILE"
echo "Envy Performance Report" >> "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
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
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv >> "$REPORT_FILE"
else
    echo "No NVIDIA GPU detected" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Python version
echo "Python Version:" >> "$REPORT_FILE"
python3 --version >> "$REPORT_FILE" 2>&1 || python --version >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# Resource usage (if Envy is running)
echo "Current Resource Usage:" >> "$REPORT_FILE"
python3 -c "
import psutil
import subprocess

# CPU
cpu_percent = psutil.cpu_percent(interval=1)
print(f'CPU Usage: {cpu_percent}%')

# Memory
memory = psutil.virtual_memory()
print(f'Memory Usage: {memory.percent}% ({memory.used / (1024**3):.2f} GB / {memory.total / (1024**3):.2f} GB)')

# GPU
try:
    result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                          capture_output=True, text=True, timeout=2)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for i, line in enumerate(lines):
            used, total = map(int, line.split(', '))
            print(f'GPU {i} Memory: {used} MB / {total} MB ({used*100/total:.1f}%)')
except:
    print('GPU: Not available or not detected')
" >> "$REPORT_FILE" 2>&1

echo "" >> "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"

cat "$REPORT_FILE"
