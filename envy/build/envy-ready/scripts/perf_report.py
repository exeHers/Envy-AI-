#!/usr/bin/env python3
"""Generate performance report for Envy."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import psutil


def gather_system_metrics(duration: int = 5):
    samples = []
    for _ in range(duration):
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()._asdict()
        sample = {
            "timestamp": time.time(),
            "cpu_percent": cpu,
            "memory_percent": mem["percent"],
            "memory_used": mem["used"],
        }
        samples.append(sample)
    return samples


def gather_gpu_metrics():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
            check=True,
            capture_output=True,
            text=True,
        )
        util, mem = result.stdout.strip().split(",")
        return {"utilization_percent": float(util), "memory_used_mb": float(mem)}
    except Exception:
        return None


def main():
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "perf-report.txt"

    samples = gather_system_metrics()
    gpu = gather_gpu_metrics()

    report_lines = [
        "Envy Performance Report",
        f"Samples collected: {len(samples)}",
        f"CPU max percent: {max(s['cpu_percent'] for s in samples):.2f}",
        f"CPU avg percent: {sum(s['cpu_percent'] for s in samples) / len(samples):.2f}",
        f"Memory peak percent: {max(s['memory_percent'] for s in samples):.2f}",
    ]
    if gpu:
        report_lines.append(f"GPU utilization percent: {gpu['utilization_percent']:.2f}")
        report_lines.append(f"GPU memory used (MB): {gpu['memory_used_mb']:.2f}")
    else:
        report_lines.append("GPU data: nvidia-smi not available.")

    report_lines.append("Raw samples:")
    report_lines.append(json.dumps(samples, indent=2))

    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"[perf] Report written to {report_path}")


if __name__ == "__main__":
    main()
