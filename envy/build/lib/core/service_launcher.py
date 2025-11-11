"""Launch multiple Envy services with one command."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

SERVICE_MODULES = [
    ("wake_listener", []),
    ("stt_service", []),
    ("skill_manager", []),
    ("tts_service", []),
    ("router_service", []),
    ("web_dashboard", []),
]


def launch_service(module: str, args: List[str], env: Dict[str, str]) -> subprocess.Popen:
    cmd = [sys.executable, "-m", f"envy.services.{module}", *args]
    return subprocess.Popen(cmd, env=env)


def launch_all(config_path: Path, profile: str, include_dashboard: bool = True) -> int:
    env = os.environ.copy()
    env["ENVY_CONFIG"] = str(config_path)
    env["ENVY_PROFILE"] = profile

    processes: List[Tuple[str, subprocess.Popen]] = []
    for module, module_args in SERVICE_MODULES:
        if not include_dashboard and module == "web_dashboard":
            continue
        proc = launch_service(module, ["--config", str(config_path)], env)
        processes.append((module, proc))
        time.sleep(0.5)  # stagger startups
        print(f"[launcher] Started {module} (pid {proc.pid})")

    def terminate_all(signum, frame):
        print(f"[launcher] Received signal {signum}. Terminating services...")
        for name, proc in processes:
            proc.terminate()
        for name, proc in processes:
            try:
                proc.wait(timeout=10)
                print(f"[launcher] {name} exited with code {proc.returncode}")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"[launcher] {name} forced to stop.")

    signal.signal(signal.SIGINT, terminate_all)
    signal.signal(signal.SIGTERM, terminate_all)

    exit_code = 0
    try:
        while True:
            alive = [proc.poll() is None for _, proc in processes]
            if not any(alive):
                exit_code = max(proc.returncode or 0 for _, proc in processes)
                break
            time.sleep(1)
    finally:
        terminate_all(signal.SIGTERM, None)
    return exit_code


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch Envy services together.")
    parser.add_argument("--config", type=str, default=str(Path(__file__).resolve().parents[2] / "config" / "envy.yaml"))
    parser.add_argument("--profile", type=str, default=os.environ.get("ENVY_PROFILE", "balanced"))
    parser.add_argument("--no-dashboard", action="store_true", help="Disable web dashboard service.")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    include_dashboard = not args.no_dashboard
    return launch_all(config_path, args.profile, include_dashboard)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

