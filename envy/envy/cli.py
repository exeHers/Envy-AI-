from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

import typer

from envy.assistant import AssistantEngine, AssistantResult, bootstrap_assistant
from envy.config_loader import ConfigError

LOGGER = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Envy assistant command line interface")

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "envy.yaml"


def _ensure_models(profile: str) -> None:
    download_script = REPO_ROOT / "scripts" / "download_models.sh"
    if not download_script.exists():
        typer.echo("Model download script missing. Please re-run installation.")
        raise typer.Exit(code=1)
    typer.echo(f"Ensuring models are available for profile '{profile}'...")
    subprocess.run(
        ["bash", str(download_script), "--profile", profile],
        cwd=REPO_ROOT,
        check=False,
    )


@app.command()
def run(
    profile: str = typer.Option("balanced", help="Runtime profile to use."),
    audio_file: Optional[Path] = typer.Option(
        None, "--audio-file", "-a", help="Process a prerecorded audio file."
    ),
    auto_confirm: bool = typer.Option(
        True, "--auto-confirm/--require-confirmation", help="Auto-approve destructive actions."
    ),
    dashboard: bool = typer.Option(
        False, "--dashboard", help="Start the web dashboard alongside processing."
    ),
) -> None:
    """Process audio once or launch the assistant loop."""

    try:
        _ensure_models(profile)
        assistant = bootstrap_assistant(
            repo_root=REPO_ROOT,
            config_path=CONFIG_PATH,
            profile=profile,
            with_dashboard=dashboard,
        )
    except ConfigError as exc:
        typer.echo(f"Configuration error: {exc}")
        raise typer.Exit(code=1) from exc

    if audio_file:
        result = assistant.process_audio_file(audio_file, auto_confirm=auto_confirm)
        typer.echo(json.dumps(result.__dict__, default=str, indent=2))
        return

    typer.echo(
        "Live microphone loop is not yet implemented in this build. "
        "Use --audio-file to run scripted demos or integrate with sounddevice."
    )


@app.command()
def download_models(profile: str = typer.Option("balanced", help="Profile to download models for")) -> None:
    """Download or verify required acoustic/LLM models."""

    _ensure_models(profile)
    typer.echo("Model assets are prepared.")


@app.command()
def list_skills() -> None:
    """List available skills."""

    assistant = bootstrap_assistant(
        repo_root=REPO_ROOT,
        config_path=CONFIG_PATH,
        profile="balanced",
        with_dashboard=False,
    )
    typer.echo("Active skills:")
    for skill in assistant.skill_manager.skills:
        typer.echo(f"- {skill.name}: {skill.description}")


if __name__ == "__main__":
    app()
