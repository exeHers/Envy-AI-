from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Dict, List

import psutil

from tests.generate_test_audio import create_audio_samples

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def collect_gpu_stats() -> Dict[str, float]:
    if not shutil.which("nvidia-smi"):
        return {}
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        util, mem_used, mem_total = result.stdout.strip().split(",")
        return {
            "gpu_util_percent": float(util.strip()),
            "gpu_mem_used_mb": float(mem_used.strip()),
            "gpu_mem_total_mb": float(mem_total.strip()),
        }
    except Exception:
        return {}


def run_sample_session() -> subprocess.Popen[str]:
    create_audio_samples()
    wake = PROJECT_ROOT / "tests" / "audio" / "wake_envy.wav"
    command_create = PROJECT_ROOT / "tests" / "audio" / "command_create_test.wav"
    cmd = [
        sys.executable,
        "-m",
        "envy.main",
        "--profile",
        "balanced",
        "--no-gui",
        "--once",
        "--simulation-grace",
        "6",
        "--simulate-audio",
        f"{wake}:{command_create}",
    ]
    env = {"PYTHONPATH": str(PROJECT_ROOT), **dict(**subprocess.os.environ)}
    process = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process


def monitor_process(process: subprocess.Popen[str]) -> Dict[str, float]:
    ps_proc = psutil.Process(process.pid)
    cpu_samples: List[float] = []
    mem_samples: List[float] = []
    start = time.time()
    while process.poll() is None:
        try:
            cpu_samples.append(ps_proc.cpu_percent(interval=0.2))
            mem_samples.append(ps_proc.memory_info().rss / (1024 * 1024))
        except psutil.NoSuchProcess:
            break
    duration = time.time() - start
    return {
        "cpu_peak_percent": max(cpu_samples) if cpu_samples else 0.0,
        "cpu_avg_percent": mean(cpu_samples) if cpu_samples else 0.0,
        "mem_peak_mb": max(mem_samples) if mem_samples else 0.0,
        "mem_avg_mb": mean(mem_samples) if mem_samples else 0.0,
        "duration_sec": duration,
    }


def write_report(output: Path, metrics: Dict[str, float], gpu: Dict[str, float], stdout: str, stderr: str) -> None:
    lines = [
        "Envy Performance Report",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "",
        "CPU:",
        f"  Peak Utilization: {metrics['cpu_peak_percent']:.2f}%",
        f"  Average Utilization: {metrics['cpu_avg_percent']:.2f}%",
        "",
        "Memory:",
        f"  Peak RSS: {metrics['mem_peak_mb']:.2f} MiB",
        f"  Average RSS: {metrics['mem_avg_mb']:.2f} MiB",
        "",
        f"Session Duration: {metrics['duration_sec']:.2f} seconds",
    ]
    if gpu:
        lines.extend(
            [
                "",
                "GPU:",
                f"  Utilization: {gpu['gpu_util_percent']:.2f}%",
                f"  Memory Used: {gpu['gpu_mem_used_mb']:.2f} MiB / {gpu['gpu_mem_total_mb']:.2f} MiB",
            ]
        )
    lines.extend(["", "Runtime stdout:", stdout.strip(), "", "Runtime stderr:", stderr.strip(), ""])
    output.write_text("\n".join(lines), encoding="utf-8")

    summary = {"cpu": metrics, "gpu": gpu, "stdout": stdout, "stderr": stderr}
    json_output = output.with_suffix(".json")
    json_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate performance report for Envy assistant.")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "artifacts" / "perf-report.txt"))
    args = parser.parse_args()

    process = run_sample_session()
    metrics = monitor_process(process)
    stdout, stderr = process.communicate(timeout=60)
    gpu_stats = collect_gpu_stats()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(output_path, metrics, gpu_stats, stdout, stderr)
    print(f"Performance report written to {output_path}")


if __name__ == "__main__":
    main()
