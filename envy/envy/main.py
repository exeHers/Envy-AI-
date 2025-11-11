from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from pathlib import Path
from typing import List, Tuple

from envy.bus import EventBus
from envy.config import Config, load_config
from envy.logging_config import setup_logging
from envy.services import (
    DashboardService,
    RouterService,
    SkillManagerService,
    SpeechToTextService,
    TextToSpeechService,
    WakeListenerService,
)
from envy.services.llm_adapter import LLMAdapter

LOGGER = logging.getLogger("envy.main")


def parse_audio_pair(pair: str) -> Tuple[str, str | None]:
    if ":" in pair:
        wake, command = pair.split(":", 1)
        return wake.strip(), command.strip() or None
    return pair.strip(), None


async def run_envy(config: Config, args: argparse.Namespace) -> None:
    paths = config.paths
    Path(paths.get("runtime_dir", "./runtime")).mkdir(parents=True, exist_ok=True)
    Path(paths.get("logs_dir", "./logs")).mkdir(parents=True, exist_ok=True)
    Path(paths.get("artifacts_dir", "./artifacts")).mkdir(parents=True, exist_ok=True)

    bus = EventBus()
    llm_adapter = LLMAdapter(config)
    services = []

    wake_service = WakeListenerService(config, bus)
    stt_service = SpeechToTextService(config, bus)
    skill_manager = SkillManagerService(config, bus)
    router_service = RouterService(config, bus, llm_adapter)
    tts_service = TextToSpeechService(config, bus)

    services.extend([wake_service, stt_service, skill_manager, router_service, tts_service])

    if not args.no_gui:
        dashboard_service = DashboardService(config, bus)
        services.append(dashboard_service)

    for service in services:
        await service.start()

    if args.simulate_audio:
        for pair in args.simulate_audio:
            wake_path, command_path = parse_audio_pair(pair)
            LOGGER.info("Injecting simulated audio wake=%s command=%s", wake_path, command_path)
            await wake_service.enqueue_audio_file(wake_path, command_path)
        if args.once:
            await asyncio.sleep(args.simulation_grace)
            return

    stop_event = asyncio.Event()

    def _handle_signal(*_: object) -> None:
        LOGGER.info("Shutdown signal received.")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:  # pragma: no cover - Windows
            signal.signal(sig, lambda *_: stop_event.set())

    await stop_event.wait()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Envy assistant runtime.")
    parser.add_argument("--profile", default="balanced", help="Runtime profile (low|balanced|power)")
    parser.add_argument("--no-gui", action="store_true", help="Disable the web dashboard")
    parser.add_argument(
        "--simulate-audio",
        action="append",
        help="Inject audio for testing in the form wake.wav[:command.wav]. Can be repeated.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Exit after processing simulated audio sequences (useful for automated tests).",
    )
    parser.add_argument(
        "--simulation-grace",
        type=float,
        default=5.0,
        help="Seconds to wait after simulation before exiting when --once is provided.",
    )
    parser.add_argument("--log-level", default="INFO", help="Root log level.")
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = load_config(profile=args.profile)
    setup_logging(config.get("paths.logs_dir", "./logs"))
    logging.getLogger().setLevel(args.log_level.upper())

    LOGGER.info("Starting Envy with profile '%s'", config.profile)

    try:
        asyncio.run(run_envy(config, args))
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user.")


if __name__ == "__main__":
    main()
