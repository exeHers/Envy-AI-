from __future__ import annotations

import subprocess
import time
from pathlib import Path
from statistics import mean

import psutil


def collect_gpu_metrics() -> dict:
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=2,
        )
        util_gpu, util_mem, mem_used, mem_total = output.strip().split(", ")
        return {
            "gpu_util_percent": float(util_gpu),
            "gpu_mem_util_percent": float(util_mem),
            "gpu_mem_used_mb": float(mem_used),
            "gpu_mem_total_mb": float(mem_total),
        }
    except Exception:
        return {}


def main():
    root = Path(__file__).resolve().parents[1]
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    report_path = artifacts / "perf-report.txt"

    cpu_samples = []
    mem_samples = []
    timestamps = []

    for _ in range(10):
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        cpu_samples.append(cpu)
        mem_samples.append(mem)
        timestamps.append(time.time())

    gpu_metrics = collect_gpu_metrics()

    report_lines = [
        "Envy Performance Report",
        f"Samples captured: {len(cpu_samples)}",
        f"CPU usage avg: {mean(cpu_samples):.2f}% (max {max(cpu_samples):.2f}%)",
        f"Memory usage avg: {mean(mem_samples):.2f}% (max {max(mem_samples):.2f}%)",
    ]

    if gpu_metrics:
        report_lines.append(
            "GPU utilization: {gpu_util_percent:.2f}% (memory {gpu_mem_used_mb:.1f}/{gpu_mem_total_mb:.1f} MB)".format(
                **gpu_metrics
            )
        )
    else:
        report_lines.append("GPU metrics unavailable (nvidia-smi not found).")

    report_lines.append(f"Timestamps: {timestamps[0]:.0f} - {timestamps[-1]:.0f}")
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
