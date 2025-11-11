#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${ROOT_DIR}/artifacts/perf-report.txt"

if [ $# -gt 0 ]; then
  DURATION="$1"
elif [ -n "${DURATION:-}" ]; then
  DURATION="${DURATION}"
else
  DURATION="15"
fi

python3 - <<'PY'
import json
import os
import subprocess
import time
from datetime import datetime

import psutil

root = os.environ["ROOT_DIR"]
output = os.environ["OUTPUT"]
duration = int(os.environ["DURATION"])

samples = []
start = time.time()
while time.time() - start < duration:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    samples.append({"timestamp": time.time(), "cpu_percent": cpu, "mem_percent": mem})

gpu_info = None
try:
    result = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
        stderr=subprocess.DEVNULL,
        text=True,
    )
    name, mem_used, mem_total, util = result.strip().split(", ")
    gpu_info = {
        "name": name,
        "memory_used_mb": float(mem_used),
        "memory_total_mb": float(mem_total),
        "utilization_percent": float(util),
    }
except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
    gpu_info = {"status": "nvidia-smi unavailable"}

report = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "duration_seconds": duration,
    "cpu_peak_percent": max(sample["cpu_percent"] for sample in samples) if samples else 0,
    "cpu_avg_percent": sum(sample["cpu_percent"] for sample in samples) / len(samples) if samples else 0,
    "memory_peak_percent": max(sample["mem_percent"] for sample in samples) if samples else 0,
    "memory_avg_percent": sum(sample["mem_percent"] for sample in samples) / len(samples) if samples else 0,
    "gpu": gpu_info,
    "samples": samples,
}

os.makedirs(os.path.dirname(output), exist_ok=True)
with open(output, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
PY

echo "Performance report saved to ${OUTPUT}"
