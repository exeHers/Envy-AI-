#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${REPO_ROOT}/artifacts/perf-report.txt"
AUDIO="${REPO_ROOT}/tests/data/wake_command.wav"

echo "[+] Generating performance report at ${OUTPUT}"

PYTHONPATH="${REPO_ROOT}" python3 - <<'PY' "$REPO_ROOT" "$AUDIO" "$OUTPUT"
import json
import os
import subprocess
import sys
import time
from datetime import datetime

import psutil

repo_root, audio_path, output_path = sys.argv[1:]
command = [sys.executable, "-m", "envy.cli", "run", "--audio-file", audio_path, "--profile", "balanced"]

env = os.environ.copy()
env["PYTHONPATH"] = repo_root

start = time.time()
proc = subprocess.Popen(
    command,
    cwd=repo_root,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=env,
)

cpu_peak = 0.0
mem_peak = 0.0
samples = []

while proc.poll() is None:
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    cpu_peak = max(cpu_peak, cpu)
    mem_peak = max(mem_peak, mem)
    samples.append({"timestamp": time.time(), "cpu": cpu, "mem": mem})

stdout, _ = proc.communicate()
duration = time.time() - start

gpu_info = ""
try:
    gpu_proc = subprocess.run(
        ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader"],
        check=True,
        capture_output=True,
        text=True,
    )
    gpu_info = gpu_proc.stdout.strip()
except Exception:
    gpu_info = "nvidia-smi not available"

report = {
    "generated": datetime.utcnow().isoformat() + "Z",
    "command": " ".join(command),
    "duration_s": round(duration, 2),
    "cpu_peak_percent": cpu_peak,
    "memory_peak_percent": mem_peak,
    "gpu": gpu_info,
    "stdout": stdout,
}

with open(output_path, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=2))

print(f"[+] Report written to {output_path}")
PY
