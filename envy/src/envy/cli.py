"""
Command-line interface for Envy assistant.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer

from .config import load_config
from .services.orchestrator import AssistantRuntime

app = typer.Typer(add_completion=False, help="Envy assistant CLI")


@app.command()
def start(
    profile: str = typer.Option("balanced", help="Resource profile (low|balanced|power)"),
    headless: bool = typer.Option(False, help="Run without starting the web dashboard"),
) -> None:
    """Start all services."""
    asyncio.run(_run(profile=profile, headless=headless))


@app.command()
def simulate(
    transcript: str = typer.Option(..., "--transcript", "-t", help="Transcript to simulate"),
) -> None:
    """Simulate a single request for testing."""
    asyncio.run(_simulate(transcript))


@app.command()
def confirm(skill: str) -> None:
    """Mark a skill as confirmed via dashboard interface."""
    runtime = AssistantRuntime()
    runtime.router.register_dashboard_confirmation(skill)
    typer.echo(f"Dashboard confirmation recorded for {skill}.")


async def _run(profile: str, headless: bool) -> None:
    runtime = AssistantRuntime(load_config(profile=profile))
    await runtime.start(headless=headless)
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        typer.echo("Received interrupt, stopping Envy...")
    finally:
        await runtime.stop()


async def _simulate(transcript: str) -> None:
    runtime = AssistantRuntime()
    outcome = await runtime.simulate_session(transcript)
    typer.echo(outcome.message)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
