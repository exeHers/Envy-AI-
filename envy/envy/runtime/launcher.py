from __future__ import annotations

import argparse
import multiprocessing
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List

import uvicorn

from ..core.config import ConfigError, load_config
from ..core.logger import setup_logging
from ..dashboard.app import DashboardConfig, create_app as create_dashboard_app
from ..services.llm_adapter.service import LLMAdapter, LLMConfig, create_app as create_llm_app
from ..services.router.service import RouterConfig, RouterService, create_app as create_router_app
from ..services.skill_manager.service import SkillManager, create_app as create_skill_app
from ..services.stt_service.service import STTConfig, STTService, create_app as create_stt_app
from ..services.tts_service.service import TTSConfig, TTSService, create_app as create_tts_app
from ..services.wake_listener.service import WakeConfig, WakeListenerService, create_app as create_wake_app


def _run_wake_service(cfg: dict, host: str, port: int):
    service = WakeListenerService(WakeConfig(**cfg))
    app = create_wake_app(service)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_stt_service(cfg: dict, host: str, port: int):
    service = STTService(STTConfig(**cfg))
    app = create_stt_app(service)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_tts_service(cfg: dict, host: str, port: int):
    cfg["artifacts_dir"] = Path(cfg["artifacts_dir"])
    service = TTSService(TTSConfig(**cfg))
    app = create_tts_app(service)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_skill_service(cfg: dict, host: str, port: int):
    manager = SkillManager(config=cfg)
    app = create_skill_app(manager)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_llm_service(cfg: dict, host: str, port: int):
    adapter = LLMAdapter(LLMConfig(**cfg))
    app = create_llm_app(adapter)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_router_service(cfg: dict, host: str, port: int):
    cfg["artifacts_dir"] = Path(cfg["artifacts_dir"])
    cfg["command_whitelist"] = tuple(cfg["command_whitelist"])
    service = RouterService(RouterConfig(**cfg))
    app = create_router_app(service)
    uvicorn.run(app, host=host, port=port, log_level="info")


def _run_dashboard_service(cfg: dict, host: str, port: int):
    cfg["artifacts_dir"] = Path(cfg["artifacts_dir"])
    cfg["logs_dir"] = Path(cfg["logs_dir"])
    app = create_dashboard_app(DashboardConfig(**cfg))
    uvicorn.run(app, host=host, port=port, log_level="info")


def launch(profile: str, config_path: str | None = None, no_dashboard: bool = False) -> None:
    config = load_config(profile=profile, config_path=Path(config_path) if config_path else None)
    profile_cfg = config["profile_config"]
    data_paths = config.get("data_paths", {})
    logs_dir = Path(data_paths.get("logs_dir", "logs")).resolve()
    artifacts_dir = Path(data_paths.get("artifacts_dir", "artifacts")).resolve()
    setup_logging(config.get("log_level", "INFO"), logs_dir=str(logs_dir))
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    service_processes: List[multiprocessing.Process] = []
    runtime = config["services"]

    wake_cfg = {
        "model_path": profile_cfg["wake"].get("model"),
        "sensitivity": profile_cfg["wake"].get("sensitivity", 0.4),
        "live_listen": not no_dashboard,
    }
    service_processes.append(
        multiprocessing.Process(
            target=_run_wake_service,
            args=(wake_cfg, config["router"]["host"], runtime["wake_listener_port"]),
            daemon=True,
        )
    )

    stt_cfg = {
        "engine": profile_cfg["stt"].get("engine", "vosk"),
        "model_path": profile_cfg["stt"].get("model"),
    }
    service_processes.append(
        multiprocessing.Process(
            target=_run_stt_service,
            args=(stt_cfg, config["router"]["host"], runtime["stt_port"]),
            daemon=True,
        )
    )

    tts_cfg = {
        "engine": profile_cfg["tts"].get("engine", "pyttsx3"),
        "voice": profile_cfg["tts"].get("voice", "default"),
        "rate": profile_cfg["tts"].get("rate", 185),
        "artifacts_dir": str(artifacts_dir),
    }
    service_processes.append(
        multiprocessing.Process(
            target=_run_tts_service,
            args=(tts_cfg, config["router"]["host"], runtime["tts_port"]),
            daemon=True,
        )
    )

    skill_cfg = {
        "enabled_skills": profile_cfg["skills"].get("enabled", []),
        "command_whitelist": config["security"].get("command_whitelist", []),
    }
    service_processes.append(
        multiprocessing.Process(
            target=_run_skill_service,
            args=(skill_cfg, config["router"]["host"], runtime["skill_manager_port"]),
            daemon=True,
        )
    )

    remote_cfg = None
    remote_root = config.get("remote_endpoints", {})
    if remote_root.get("enabled"):
        providers = remote_root.get("providers", [])
        if providers:
            remote_cfg = providers[0]

    llm_cfg = {
        "provider": profile_cfg["llm"].get("provider", "stub"),
        "model_path": profile_cfg["llm"].get("model_path"),
        "max_tokens": profile_cfg["llm"].get("max_tokens", 256),
        "gpu_layers": profile_cfg["llm"].get("gpu_layers", 0),
        "remote": remote_cfg,
    }
    service_processes.append(
        multiprocessing.Process(
            target=_run_llm_service,
            args=(llm_cfg, config["router"]["host"], runtime["llm_adapter_port"]),
            daemon=True,
        )
    )

    router_cfg = {
        "persona": config.get("persona", "neutral-sardonic"),
        "stt_url": f"http://{config['router']['host']}:{runtime['stt_port']}",
        "skill_url": f"http://{config['router']['host']}:{runtime['skill_manager_port']}",
        "tts_url": f"http://{config['router']['host']}:{runtime['tts_port']}",
        "llm_url": f"http://{config['router']['host']}:{runtime['llm_adapter_port']}",
        "artifacts_dir": str(artifacts_dir),
        "command_whitelist": config["security"].get("command_whitelist", []),
    }
    service_processes.append(
        multiprocessing.Process(
            target=_run_router_service,
            args=(router_cfg, config["router"]["host"], config["router"]["port"]),
            daemon=True,
        )
    )

    if not no_dashboard:
        dashboard_cfg = {
            "router_url": f"http://{config['router']['host']}:{config['router']['port']}",
            "artifacts_dir": str(artifacts_dir),
            "logs_dir": str(logs_dir),
        }
        service_processes.append(
            multiprocessing.Process(
                target=_run_dashboard_service,
                args=(dashboard_cfg, config["dashboard"]["host"], config["dashboard"]["port"]),
                daemon=True,
            )
        )

    for process in service_processes:
        process.start()
        time.sleep(0.5)

    def _terminate(signum, frame):
        for proc in service_processes:
            if proc.is_alive():
                proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGINT, _terminate)

    for process in service_processes:
        process.join()


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch Envy services")
    parser.add_argument("--profile", default="balanced", help="Runtime profile (low|balanced|power)")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable dashboard and live wake listening")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    try:
        launch(profile=args.profile, config_path=args.config, no_dashboard=args.no_dashboard)
    except ConfigError as exc:
        print(f"Failed to launch Envy: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
