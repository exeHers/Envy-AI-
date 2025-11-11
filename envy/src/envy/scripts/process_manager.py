from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List

import typer

from envy.services.common.config import DEFAULT_CONFIG_PATH

app = typer.Typer(add_completion=False, help="Manage Envy microservices.")


BASE_SERVICES = [
    ("wake_listener", "envy.services.wake_listener.main:app", 8201),
    ("stt_service", "envy.services.stt_service.main:app", 8202),
    ("router", "envy.services.router.main:app", 8203),
    ("skill_manager", "envy.services.skill_manager.main:app", 8204),
    ("tts_service", "envy.services.tts_service.main:app", 8205),
]

WEB_SERVICE = ("web_dashboard", "envy.services.web_dashboard.main:app", 8300)


def _build_command(module: str, port: int, host: str = "0.0.0.0") -> List[str]:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        module,
        "--host",
        host,
        "--port",
        str(port),
    ]


@app.command()
def start(
    profile: str = typer.Option("balanced", "--profile", help="Runtime profile (low, balanced, power)."),
    include_dashboard: bool = typer.Option(True, "--dashboard/--no-dashboard", help="Start the web dashboard."),
    config_path: Path = typer.Option(DEFAULT_CONFIG_PATH, "--config", help="Path to envy.yaml config."),
) -> None:
    env = os.environ.copy()
    env["ENVY_PROFILE"] = profile
    env["ENVY_CONFIG_PATH"] = str(config_path)

    services = list(BASE_SERVICES)
    if include_dashboard:
        services.append(WEB_SERVICE)

    processes: List[subprocess.Popen] = []
    typer.echo(f"[Envy] Starting services with profile '{profile}'")
    try:
        for name, module, port in services:
            cmd = _build_command(module, port)
            typer.echo(f"[Envy] Launching {name} on port {port}")
            proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(proc)
            time.sleep(0.3)

        typer.echo("[Envy] All services started. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            for proc in processes:
                if proc.poll() is not None:
                    typer.echo(f"[Envy] Service exited with code {proc.returncode}, shutting down.")
                    raise typer.Exit(code=proc.returncode or 1)
    except KeyboardInterrupt:
        typer.echo("[Envy] Stopping services...")
    finally:
        for proc in processes:
            if proc.poll() is None:
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                except OSError:
                    continue
        time.sleep(1)
        for proc in processes:
            if proc.poll() is None:
                try:
                    os.kill(proc.pid, signal.SIGKILL)
                except OSError:
                    continue
        typer.echo("[Envy] Shutdown complete.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
