from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import typer
import uvicorn

from services.config import load_config, resolve_profile
from services.logger import get_logger
from services.router import EnvyRouter
from services.web_dashboard import create_app


cli = typer.Typer(add_completion=False)
logger = get_logger("cli")


@cli.command()
def demo(
    profile: str = typer.Option("balanced", help="Runtime profile defined in config/envy.yaml"),
    wake_audio: Path = typer.Option(Path("data/audio_samples/wake_envy.wav"), help="Wake word sample."),
    command_audio: Path = typer.Option(Path("data/audio_samples/command_create_test.wav"), help="Command audio sample."),
    output: Path = typer.Option(Path("artifacts/demo_result.json"), help="Where to persist the demo result."),
):
    """
    Run an end-to-end demo using prerecorded audio files.
    """
    router = EnvyRouter(profile=profile)
    result = router.handle_audio_session(wake_audio, command_audio)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.__dict__, indent=2), encoding="utf-8")
    typer.echo(output.read_text())


@cli.command()
def start(
    profile: str = typer.Option("balanced"),
    host: str = typer.Option("0.0.0.0"),
    port: int = typer.Option(8420),
    no_gui: bool = typer.Option(False, "--no-gui", help="Disable the web dashboard."),
):
    """
    Start the Envy assistant runtime loop.
    """
    config = load_config()
    runtime = resolve_profile(config, profile)
    logger.info("Starting Envy runtime with profile %s", runtime["resolved_profile"])
    router = EnvyRouter(profile=profile)

    stop_event = threading.Event()

    def dashboard_thread():
        app = create_app()
        uvicorn.run(app, host=host, port=port, log_level="info")

    if not no_gui and runtime["runtime"]["enable_dashboard"]:
        thread = threading.Thread(target=dashboard_thread, daemon=True)
        thread.start()
        logger.info("Web dashboard available at http://%s:%d", host, port)

    try:
        typer.echo("Envy is standing by. Press Ctrl+C to exit.")
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        typer.echo("Stopping Envy runtime...")
        stop_event.set()


if __name__ == "__main__":
    cli()
