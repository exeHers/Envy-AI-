#!/usr/bin/env python3
"""
Generate a lightweight performance report for Envy.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from datetime import datetime

import psutil

from envy.config import load_config
from envy.services.orchestrator import AssistantRuntime


async def main() -> None:
    config = load_config()
    runtime = AssistantRuntime(config)

    cpu_before = psutil.cpu_percent(interval=0.1)
    mem_before = psutil.virtual_memory().percent
    gpu_info = query_gpu()

    start = datetime.utcnow()
    outcome = await runtime.simulate_session("Envy, create test.py that prints hello from envy")
    duration = (datetime.utcnow() - start).total_seconds()

    cpu_after = psutil.cpu_percent(interval=0.1)
    mem_after = psutil.virtual_memory().percent

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "wake_word": "simulated",
        "cpu_percent_before": cpu_before,
        "cpu_percent_after": cpu_after,
        "memory_percent_before": mem_before,
        "memory_percent_after": mem_after,
        "gpu": gpu_info,
        "latency_seconds": duration,
        "outcome": outcome.message,
    }

    print(json.dumps(report, indent=2))


def query_gpu():
    if not shutil.which("nvidia-smi"):
        return {"available": False}
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.total,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        gpu_util, mem_total, mem_used = result.stdout.strip().split(", ")
        return {
            "available": True,
            "util_percent": float(gpu_util),
            "memory_total_mb": float(mem_total),
            "memory_used_mb": float(mem_used),
        }
    except Exception as exc:  # pragma: no cover
        return {"available": False, "error": str(exc)}


if __name__ == "__main__":
    asyncio.run(main())
